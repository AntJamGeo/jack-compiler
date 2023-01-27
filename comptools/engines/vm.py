import os

from comptools.engines._base import CompilationEngine
from comptools._writers import VMWriter
from comptools._symboltable import SymbolTable


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

    # ---------------------COMPILATION FUNCTIONS---------------------
    def _compile_class(self):
        """
        Compiles code of the form:
            'class' className '{' classVarDec* subroutineDec* '}'
        """
        self._symboltable = SymbolTable()
        self._assert_token("class")
        self._assert_identifier("class")
        self._assert_token("{")
        self._compile_class_var_dec()
        self._compile_subroutine()
        self._assert_token("}")
        if self._tokenizer.has_more_tokens:
            self._raise_error(
                "Class",
                "All code should be within a single class block."
            )

    def _compile_class_var_dec(self):
        """
        Compiles code of the form:
            ('static' | 'field') type varName (',' varName)* ';'
        """
        while self._tokenizer.token in _CLASS_VAR_DEC_KEYWORDS:
            kind = self._get_assert()
            if kind == "field":
                kind = "this"
            type_ = self._get_assert(self._assert_type)
            self._define(type_, kind)
            while self._check_token(","):
                self._define(type_, kind)
            self._assert_token(";")

    def _compile_subroutine(self):
        """
        Compiles code of the form:
            ('constructor' | 'function' | 'method') ('void' | type)
            subroutineName '(' parameterList ')' subroutineBody
        """
        while self._tokenizer.token in _SUBROUTINE_DEC_KEYWORDS:
            self._symboltable.start_subroutine()
            subroutine_category = self._tokenizer.token
            self._tokenizer.advance()
            self._assert_subroutine_type()
            self._assert_identifier(subroutine_category)
            self._assert_token("(")
            self._compile_parameter_list()
            self._assert_token(")")
            # subroutineBody of form:
                # '{' varDec* statements '}'
            self._assert_token("{")
            self._compile_var_dec()
            self._compile_statements()
            self._assert_token("}")

    def _compile_parameter_list(self):
        """
        Compiles code of the form:
            ( (type varName) (',' type varName)*)?
        """

        if (self._tokenizer.token in _TYPE_KEYWORDS
                or self._tokenizer.token_type == "identifier"):
            type_ = self._get_assert()
            self._define(type_, "argument")
            while self._check_token(","):
                type_ = self._get_assert()
                self._define(type_, "argument")

    def _compile_var_dec(self):
        """
        Compiles code of the form:
            'var' type varName (',' varName)* ';'
        """
        while self._check_token("var"):
            type_ = self._get_assert(self._assert_type)
            self._define(type_, "local")
            while self._check_token(","):
                self._define(type_, "local")
            self._assert_token(";")

    def _compile_statements(self):
        """
        Compiles a series of statements, which must begin with the
        keywords: 'let', 'if', 'while', 'do', or 'return'.
        """
        while True:
            if self._check_token("let"):
                self._compile_let()
            elif self._check_token("if"):
                self._compile_if()
            elif self._check_token("while"):
                self._compile_while()
            elif self._check_token("do"):
                self._compile_do()
            elif self._check_token("return"):
                self._compile_return()
            else:
                return

    def _compile_let(self):
        """
        Compile code of the form:
            'let' varName ('[' expression ']')? '=' expression ';'
        """
        name = self._get_assert(self._assert_identifier)
        if self._check_token("["):
            self._compile_expression()
            self._assert_token("]")
        self._assert_token("=")
        self._compile_expression()
        self._assert_token(";")

    def _compile_if(self):
        """
        Compile code of the form:
            'if' '(' expression ')' '{' statements '}'
            ('else' '{' statements '}')?
        """
        self._assert_token("(")
        self._compile_expression()
        self._assert_token(")")
        self._assert_token("{")
        self._compile_statements()
        self._assert_token("}")
        if self._check_token("else"):
            self._assert_token("{")
            self._compile_statements()
            self._assert_token("}")

    def _compile_while(self):
        """
        Compile code of the form:
            'while' '(' expression ')' '{' statements '}'
        """
        self._assert_token("(")
        self._compile_expression()
        self._assert_token(")")
        self._assert_token("{")
        self._compile_statements()
        self._assert_token("}")

    def _compile_do(self):
        """
        Compile code of the form:
            'do' subroutineCall ';'
        """
        # subroutineCall of form:
            # ((className | varName) '.')?
            # subroutineName '(' expressionList ')'
        self._assert_identifier(advance=False)
        subroutine = self._tokenizer.token
        self._tokenizer.advance()
        if self._check_token(".", advance=False):
            self._tokenizer.advance()
            self._assert_identifier(advance=False)
            subroutine = ".".join([subroutine, self._tokenizer.token])
            self._tokenizer.advance()
        self._write(token_type="subroutine", token=subroutine, advance=False)
        self._assert_token("(")
        self._compile_expression_list()
        self._assert_token(")")
        self._assert_token(";")

    def _compile_return(self):
        """
        Compile code of the form:
            'return' expression? ';'
        """
        if self._tokenizer.token != ";":
            self._compile_expression()
        self._assert_token(";")

    def _compile_expression(self):
        """
        Compile code of the form:
            term (op term)*
        """
        self._compile_term()
        while self._check_token(_OPS, advance=False):
            op = self._get_assert()
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
            self._tokenizer.advance()
        elif self._tokenizer.token_type == "stringConstant":
            string = self._get_assert()
            self._writer.push("constant", len(string))
            self._writer.call("String.new", 1)
            for c in string:
                self._writer.push("constant", ord(c))
                self._writer.call("String.appendChar", 1)
        elif self._check_token("true"):
            self._writer.push("constant", 0)
            self._writer.arithmetic("not")
        elif self._check_token(_ZERO_CONSTANTS):
            self._writer.push("constant", 0)
        elif self._check_token("this"):
            self._writer.push("pointer", 0)
        elif self._tokenizer.token_type == "identifier":
            name = self._get_assert()
            if self._check_token("."):
                subroutine = self._get_assert(self._assert_identifier)
                name = ".".join([name, subroutine])
                self._assert_token("(")
                n_args = self._compile_expression_list()
                self._assert_token(")")
                self._writer.call(name, n_args)
            elif self._check_token("[", advance=False):
                arr = self._get_var(name, prev=True)
                self._tokenizer.advance()
                self._writer.push(arr["kind"], arr["index"])
                self._compile_expression()
                self._writer.arithmetic("add")
                self._writer.pop("pointer", 1)
                self._writer.push("that", 0)
                self._assert_token("]")
            else:
                var = self._get_var(name, prev=True)
                self._writer.push(var["kind"], var["index"])
        elif self._check_token("("):
            self._compile_expression()
            self._assert_token(")")
        elif self._check_token("-"):
            self._compile_term()
            self._writer.arithmetic("neg")
        elif self._check_token("~"):
            self._compile_term()
            self._writer.arithmetic("not")

    def _compile_expression_list(self):
        """
        Compile code of the form:
            (expression (',' expression)*)?
        """
        n = 0
        if (self._tokenizer.token in _TYPE_TOKENS
                or self._tokenizer.token_type in _TYPE_TYPES):
            self._compile_expression()
            n += 1
            while self._check_token(","):
                self._compile_expression()
                n += 1
        return n

    # -----------------------WRITING FUNCTIONS-----------------------
    def _write(self, stuff=".", advance=True, *args, **kwargs):
        self._writer.write(stuff)
        if advance:
            self._tokenizer.advance()

    def _open_block(self, block):
        pass

    def _close_block(self, block):
        pass
    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_token(self, token, advance=True, prev=False):
        super()._assert_token(token, prev)
        if advance:
            self._tokenizer.advance()

    def _assert_identifier(self, advance=True, prev=False):
        super()._assert_identifier(prev)
        if advance:
            self._tokenizer.advance()

    def _assert_type(self, advance=True, prev=False):
        super()._assert_type(prev)
        if advance:
            self._tokenizer.advance()

    def _assert_subroutine_type(self, advance=True, prev=False):
        super()._assert_subroutine_type(prev)
        if advance:
            self._tokenizer.advance()

    # ----------------------CHECKING FUNCTIONS-----------------------
    def _check_token(self, token, advance=True):
        if type(token) is str:
            success = self._tokenizer.token == token
        else:
            success = self._tokenizer.token in token
        if success:
            if advance:
                self._tokenizer.advance()
            return True
        return False

    # ------------------------OTHER FUNCTIONS------------------------
    def _define(self, type_, kind):
        name = self._get_assert(self._assert_identifier)
        self._symboltable.define(name, type_, kind)

    def _get_assert(self, assertion=None, prev=False):
        val = self._tokenizer.token
        if assertion is None:
            self._tokenizer.advance()
        else:
            assertion(prev=prev)
        return val

    def _get_var(self, name, prev=False):
        var = self._symboltable.get_var(name)
        if var is None:
            self._raise_error(
                "Variable",
                f"Variable '{name}' has not been declared.",
                prev
            )
        return var


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_ZERO_CONSTANTS = frozenset(("false", "null"))
_UNARY_OPS = frozenset("-~")
_OPS = frozenset("+-*/&|<>=")
_BIN_OP_MAP = {
    "+": "add",
    "-": "sub",
    "&": "and",
    "|": "or",
    "<": "lt",
    ">": "gt",
    "=": "eq"
}
_TYPE_TOKENS = frozenset("(") | _UNARY_OPS | _KEYWORD_CONSTANTS
_TYPE_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
