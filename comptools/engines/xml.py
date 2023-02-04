import os

from comptools.engines._base import CompilationEngine
from comptools._writers import XMLWriter


class XMLCompilationEngine(CompilationEngine):
    """
    Compile a .jack file into a .xml file showing each token.

    Methods
    -------
    run()
        Compile the .jack file provided on initialisation to xml.
    """
    def __init__(self):
        super().__init__(XMLWriter())
        self._symboltable = None

    # ---------------------COMPILATION FUNCTIONS---------------------
    def _compile_class(self):
        """
        Compiles code of the form:
            'class' className '{' classVarDec* subroutineDec* '}'
        """
        self._open_block("class")
        super()._compile_class()
        self._close_block("class")

    def _compile_class_var_dec(self):
        """
        Compiles code of the form:
            (('static' | 'field') type varName (',' varName)* ';')*
        """
        self._open_block("classVarDec")
        super()._compile_class_var_dec()
        self._close_block("classVarDec")

    def _compile_subroutine(self):
        """
        Compiles code of the form:
            ('constructor' | 'function' | 'method') ('void' | type)
            subroutineName '(' parameterList ')' subroutineBody
        """
        self._open_block("subroutineDec")
        self._symboltable.start_subroutine()
        kind = self._absorb()
        self._absorb(":subroutine_type")
        self._absorb(":identifier", tag="subroutineName")
        if kind == "method":
            self._symboltable.define("this", self._class_name, "argument")
        self._absorb("(")
        self._compile_parameter_list()
        self._absorb(")")
        # subroutineBody of form:
            # '{' varDec* statements '}'
        self._open_block("subroutineBody")
        self._absorb("{")
        while self._tokenizer.token == "var":
            self._compile_var_dec()
        self._compile_statements()
        self._absorb("}")
        self._close_block("subroutineBody")
        self._close_block("subroutineDec")

    def _compile_parameter_list(self):
        """
        Compiles code of the form:
            ( (type varName) (',' type varName)*)?
        """
        self._open_block("parameterList")
        super()._compile_parameter_list()
        self._close_block("parameterList")

    def _compile_var_dec(self):
        """
        Compiles code of the form:
            'var' type varName (',' varName)* ';'
        """
        self._open_block("varDec")
        super()._compile_var_dec()
        self._close_block("varDec")

    def _compile_statements(self):
        """
        Compiles a series of statements, which must begin with the
        keywords: 'let', 'if', 'while', 'do', or 'return'.
        """
        self._open_block("statements")
        super()._compile_statements()
        self._close_block("statements")

    def _compile_let(self):
        """
        Compile code of the form:
            'let' varName ('[' expression ']')? '=' expression ';'
        """
        self._open_block("letStatement")
        self._absorb("let")

        # save the current state so that if there is an error, the
        # error message will accurately show where the error is
        state = self._tokenizer.state
        var = self._symboltable.get_var(self._tokenizer.token)
        if var is None:
            self._raise_var_error()
        var_tag = generate_var_tag(var)
        self._absorb(":identifier", tag=var_tag)
        if self._tokenizer.token == "[":
            if var["type"] != "Array":
                self._raise_array_error(state)
            self._absorb()
            self._compile_expression()
            self._absorb("]")
        self._absorb("=")
        self._compile_expression()
        self._absorb(";")
        self._close_block("letStatement")

    def _compile_if(self):
        """
        Compile code of the form:
            'if' '(' expression ')' '{' statements '}'
            ('else' '{' statements '}')?
        """
        self._open_block("ifStatement")
        self._absorb("if")
        self._absorb("(")
        self._compile_expression()
        self._absorb(")")
        self._absorb("{")
        self._compile_statements()
        self._absorb("}")
        if self._tokenizer.token == "else":
            self._absorb()
            self._absorb("{")
            self._compile_statements()
            self._absorb("}")
        self._close_block("ifStatement")

    def _compile_while(self):
        """
        Compile code of the form:
            'while' '(' expression ')' '{' statements '}'
        """
        self._open_block("whileStatement")
        self._absorb("while")
        self._absorb("(")
        self._compile_expression()
        self._absorb(")")
        self._absorb("{")
        self._compile_statements()
        self._absorb("}")
        self._close_block("whileStatement")

    def _compile_do(self):
        """
        Compile code of the form:
            'do' subroutineCall ';'
        """
        self._open_block("doStatement")
        self._absorb("do")

        # save the current state so that if there is an error, the
        # error message will accurately show where the error is
        state = self._tokenizer.state
        super()._absorb(":identifier")
        if not self._compile_subroutine_call(state.token):
            raise self._raise_subroutine_error(state)

        self._absorb(";")
        self._close_block("doStatement")

    def _compile_return(self):
        """
        Compile code of the form:
            'return' expression? ';'
        """
        self._open_block("returnStatement")
        self._absorb("return")
        if self._tokenizer.token != ";":
            self._compile_expression()
        self._absorb(";")
        self._close_block("returnStatement")

    def _compile_expression(self):
        """
        Compile code of the form:
            term (op term)*
        """
        self._open_block("expression")
        self._compile_term()
        while self._is_binary_op():
            self._absorb()
            self._compile_term()
        self._close_block("expression")

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
        self._open_block("term")
        if (self._tokenizer.token_type == "integerConstant"
                or self._tokenizer.token_type == "stringConstant"
                or self._is_keyword_constant()):
            self._absorb()
        elif self._tokenizer.token_type == "identifier":
            # save the current state so that if there is an error, the
            # error message will accurately show where the error is
            state = self._tokenizer.state
            super()._absorb(":identifier")
            if not self._compile_subroutine_call(state.token):
                # if not a subroutine call, we have a variable
                var = self._symboltable.get_var(state.token)
                if var is None:
                    self._raise_var_error(state)
                var_tag = generate_var_tag(var)
                self._write(tag=var_tag, token=state.token)
                # if we have an open square bracket afterwards, this
                # is an array
                if self._tokenizer.token == "[":
                    if var["type"] != "Array":
                        self._raise_array_error(state)
                    self._absorb()
                    self._compile_expression()
                    self._absorb("]")
        elif self._tokenizer.token == "(":
            self._absorb()
            self._compile_expression()
            self._absorb(")")
        elif self._is_unary_op():
            self._absorb()
            self._compile_term()
        self._close_block("term")

    def _compile_expression_list(self):
        """
        Compile code of the form:
            (expression (',' expression)*)?
        """
        self._open_block("expressionList")
        if self._is_term():
            self._compile_expression()
            while self._tokenizer.token == ",":
                self._absorb()
                self._compile_expression()
        self._close_block("expressionList")

    def _compile_subroutine_call(self, name):
        """
        Compilie code of the form
            ((className | varName) '.')?
            subroutineName '(' expressionList ')'
        """
        local_method = True
        # If there is a '.', we have a class subroutine or a method
        # applied to a variable. Otherwise, we have a local
        # method call.
        if self._tokenizer.token == ".":
            super()._absorb()
            subroutine = super()._absorb(":identifier")
            var = self._symboltable.get_var(name)
            # if name does not match any variable in the symbol table,
            # it must be a class name
            if var is None:
                self._write(tag="className", token=name)
            # otherwise we know it is a variable name
            else:
                var_tag = generate_var_tag(var)
                self._write(tag=var_tag, token=name)
            self._write("symbol", ".")
            self._write("subroutineName", subroutine)
            local_method = False
        if self._tokenizer.token == "(":
            if local_method:
                self._write("subroutineName", name)
            self._absorb("(")
            self._compile_expression_list()
            self._absorb(")")
            return True
        return False

    # -----------------------WRITING FUNCTIONS-----------------------
    def _absorb(self, mode=None, tag=None):
        if mode == ":identifier":
            if tag is None:
                raise TypeError(
                    "_absorb() missing required argument 'tag'"
                )
            self._write(tag=tag)
        elif mode == ":var_dec":
            var = self._symboltable.get_var(self._tokenizer.token)
            self._write(tag=generate_var_tag(var))
        elif ((mode == ":var_type" or mode == ":subroutine_type")
                and self._tokenizer.token == "identifier"):
            self._write(tag="className")
        else:
            self._write()
        return super()._absorb(mode)

    def _write(self, tag=None, token=None):
        if tag is None:
            tag = self._tokenizer.token_type
        if token is None:
            token = self._tokenizer.token
        self._writer.write(tag, token)

    def _open_block(self, block):
        self._writer.open_block(block)

    def _close_block(self, block):
        self._writer.close_block(block)


def generate_var_tag(var):
    return f"{var['kind']}.{var['type']}.{var['index']}"

