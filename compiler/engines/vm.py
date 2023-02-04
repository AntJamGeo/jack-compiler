import os

from engines._base import CompilationEngine
from _writers import VMWriter


class VMCompilationEngine(CompilationEngine):
    """
    Compile a .jack file into virtual machine code.

    Methods
    -------
    run()
        Compile the .jack file provided on initialisation into
        virtual machine code.
    """
    def __init__(self):
        super().__init__(VMWriter())
        self._symboltable = None
        self._branch_count = 0

    # ---------------------COMPILATION FUNCTIONS---------------------
    def _compile_subroutine(self):
        """
        Compiles code of the form:
            ('constructor' | 'function' | 'method') ('void' | type)
            subroutineName '(' parameterList ')' subroutineBody
        """
        self._symboltable.start_subroutine()
        kind = self._absorb()
        self._absorb(":subroutine_type")
        name = self._absorb(":identifier")
        full_name = ".".join([self._class_name, name])
        if kind == "method":
            self._symboltable.define("this", self._class_name, "argument")
        self._absorb("(")
        self._compile_parameter_list()
        self._absorb(")")
        # subroutineBody of form:
            # '{' varDec* statements '}'
        self._absorb("{")
        while self._tokenizer.token == "var":
            self._compile_var_dec()

        # after adding all local variables to the symbol table, we know
        # how many local variables there are so we can write the VM
        # function command
        self._writer.function(
            full_name, self._symboltable.var_count["local"])
        # for constructors, we need to allocate memory; the number of
        # 16-bit words we need is equal to the number of fields
        if kind == "constructor":
            self._writer.push(
                "constant", self._symboltable.var_count["this"])
            self._writer.call("Memory.alloc", 1)
            self._writer.pop("pointer", 0)
        # for methods, we push argument 0 (i.e. the current object) and
        # pop it to pointer 0 so that the 'this' segment is aligned
        # with the object
        elif kind == "method":
            self._writer.push("argument", 0)
            self._writer.pop("pointer", 0)

        self._compile_statements()
        self._absorb("}")

    def _compile_let(self):
        """
        Compile code of the form:
            'let' varName ('[' expression ']')? '=' expression ';'
        """
        self._absorb("let")

        # save the current state so that if there is an error, the
        # error message will accurately show where the error is
        state = self._tokenizer.state
        var = self._symboltable.get_var(self._tokenizer.token)
        if var is None:
            self._raise_var_error()
        self._absorb(":identifier")
        is_arr = False
        if self._tokenizer.token == "[":
            if var["type"] != "Array":
                self._raise_array_error(state)
            self._absorb()
            is_arr = True
            # for array access, take the base location of the array
            # and add it to the value of the expression in the brackets
            self._writer.push(var["kind"], var["index"])
            self._compile_expression()
            self._writer.arithmetic("add")
            self._absorb("]")
        self._absorb("=")
        self._compile_expression()
        if is_arr:
            self._writer.pop("temp", 0)
            self._writer.pop("pointer", 1)
            self._writer.push("temp", 0)
            self._writer.pop("that", 0)
        else:
            self._writer.pop(var["kind"], var["index"])
        self._absorb(";")

    def _compile_if(self):
        """
        Compile code of the form:
            'if' '(' expression ')' '{' statements '}'
            ('else' '{' statements '}')?
        """
        self._absorb("if")
        self._branch_count += 1
        else_label = f"ELSE_BRANCH.{self._branch_count}"
        end_label = f"END_BRANCH.{self._branch_count}"
        self._absorb("(")
        self._compile_expression()
        self._absorb(")")
        self._writer.arithmetic("not")
        self._writer.if_goto(else_label)
        self._absorb("{")
        self._compile_statements()
        self._absorb("}")
        self._writer.goto(end_label)
        self._writer.label(else_label)
        if self._tokenizer.token == "else":
            self._absorb()
            self._absorb("{")
            self._compile_statements()
            self._absorb("}")
        self._writer.label(end_label)

    def _compile_while(self):
        """
        Compile code of the form:
            'while' '(' expression ')' '{' statements '}'
        """
        self._absorb("while")
        self._branch_count += 1
        loop_label = f"LOOP_BRANCH.{self._branch_count}"
        break_label = f"BREAK_BRANCH.{self._branch_count}"
        self._writer.label(loop_label)
        self._absorb("(")
        self._compile_expression()
        self._absorb(")")
        self._writer.arithmetic("not")
        self._writer.if_goto(break_label)
        self._absorb("{")
        self._compile_statements()
        self._absorb("}")
        self._writer.goto(loop_label)
        self._writer.label(break_label)

    def _compile_do(self):
        """
        Compile code of the form:
            'do' subroutineCall ';'
        """
        self._absorb("do")

        # save the current state so that if there is an error, the
        # error message will accurately show where the error is
        state = self._tokenizer.state
        self._absorb(":identifier")
        if not self._compile_subroutine_call(state.token):
            raise self._raise_subroutine_error(state)

        # throw away the return value at the end of a do statement
        self._writer.pop("temp", 0)

        self._absorb(";")

    def _compile_return(self):
        """
        Compile code of the form:
            'return' expression? ';'
        """
        self._absorb("return")
        if self._tokenizer.token != ";":
            self._compile_expression()
            self._writer.ret()
        else:
            self._writer.push("constant", 0)
            self._writer.ret()
        self._absorb(";")

    def _compile_expression(self):
        """
        Compile code of the form:
            term (op term)*
        """
        self._compile_term()
        while self._is_binary_op():
            op = self._absorb()
            self._compile_term()
            if op == "*":
                self._writer.call("Math.multiply", 2)
            elif op == "/":
                self._writer.call("Math.divide", 2)
            else:
                self._writer.arithmetic(_BIN_OP_MAP[op])

    def _compile_term(self):
        """
        Compile a term, which can be one of the following:
            - integerConstant
            - stringConstant
            - keywordConstant
            - varName
            - varName '[' expression ']'
            - subroutineCall
            - '(' expression ')'
            - unaryOp term
        """
        if self._tokenizer.token_type == "integerConstant":
            self._writer.push("constant", self._tokenizer.token)
            self._absorb()
        elif self._tokenizer.token_type == "stringConstant":
            string = self._absorb()
            self._writer.push("constant", len(string))
            self._writer.call("String.new", 1)
            for c in string:
                self._writer.push("constant", ord(c))
                self._writer.call("String.appendChar", 2)
        elif self._is_keyword_constant():
            if self._tokenizer.token == "true":
                self._absorb()
                self._writer.push("constant", 0)
                self._writer.arithmetic("not")
            elif self._tokenizer.token == "this":
                self._absorb()
                self._writer.push("pointer", 0)
            # if not 'true' or 'this', must be 'false' or 'null',
            # which are both constant values of 0
            else:
                self._absorb()
                self._writer.push("constant", 0)
        elif self._tokenizer.token_type == "identifier":
            # save the current state so that if there is an error, the
            # error message will accurately show where the error is
            state = self._tokenizer.state
            self._absorb(":identifier")
            if not self._compile_subroutine_call(state.token):
                var = self._symboltable.get_var(state.token)
                if var is None:
                    self._raise_var_error(state)
                self._writer.push(var["kind"], var["index"])
                if self._tokenizer.token == "[":
                    if var["type"] != "Array":
                        self._raise_array_error(state)
                    self._absorb()
                    # for array access, take the base location of the
                    # array and add it to the value of the expression
                    # in the brackets
                    self._compile_expression()
                    self._writer.arithmetic("add")
                    # popping the location onto pointer 1 aligns the
                    # 'that' segment with the desired part of the
                    # array, so the value can be pushed onto the stack
                    # from that 0
                    self._writer.pop("pointer", 1)
                    self._writer.push("that", 0)
                    self._absorb("]")
        elif self._tokenizer.token == "(":
            self._absorb()
            self._compile_expression()
            self._absorb(")")
        elif self._tokenizer.token == "-":
            self._absorb()
            self._compile_term()
            self._writer.arithmetic("neg")
        elif self._tokenizer.token == "~":
            self._absorb()
            self._compile_term()
            self._writer.arithmetic("not")

    def _compile_expression_list(self):
        """
        Compile code of the form:
            (expression (',' expression)*)?
        """
        # we keep a count of the number of expressions so that we know
        # how many arguments have been input to a subroutine call
        n = 0
        if self._is_term():
            self._compile_expression()
            n += 1
            while self._tokenizer.token == ",":
                self._absorb()
                self._compile_expression()
                n += 1
        return n

    def _compile_subroutine_call(self, name):
        """
        Compilie code of the form
            ((className | varName) '.')?
            subroutineName '(' expressionList ')'
        """
        n_args = 0
        local_method = True
        # If there is a '.', we have a class subroutine or a method
        # applied to a variable. Otherwise, we have a local
        # method call.
        if self._tokenizer.token == ".":
            self._absorb()
            subroutine = self._absorb(":identifier")
            var = self._symboltable.get_var(name)
            # if name does not match any variable in the symbol table,
            # it must be a class name
            if var is None:
                name = ".".join([name, subroutine])
            # otherwise we know it is a variable name
            else:
                name = ".".join([var["type"], subroutine])
                self._writer.push(var["kind"], var["index"])
                n_args = 1
            local_method = False
        if self._tokenizer.token == "(":
            if local_method:
                name = ".".join([self._class_name, name])
                self._writer.push("pointer", 0)
                n_args = 1
            self._absorb()
            n_args += self._compile_expression_list()
            self._absorb(")")
            self._writer.call(name, n_args)
            return True
        return False


_ZERO_CONSTANTS = frozenset(("false", "null"))
_BIN_OP_MAP = {
    "+": "add",
    "-": "sub",
    "&": "and",
    "|": "or",
    "<": "lt",
    ">": "gt",
    "=": "eq"
}
