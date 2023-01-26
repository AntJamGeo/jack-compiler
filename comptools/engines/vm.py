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
        self._symboltable = SymbolTable()

    # ---------------------COMPILATION FUNCTIONS---------------------
    def _compile_class(self):
        """
        Compiles code of the form:
            'class' className '{' classVarDec* subroutineDec* '}'
        """
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
            self._define(type_, "var")
            while self._check_token(","):
                self._define(type_, "var")
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
        self._assert_identifier("var")
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
        self._open_block("expression")
        self._compile_term()
        while self._check_token(_OPS):
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
                or self._tokenizer.token in _KEYWORD_CONSTANTS):
            self._write()
        elif self._tokenizer.token_type == "identifier":
            name = self._tokenizer.token
            self._tokenizer.advance()
            if self._check_token(".", advance=False):
                self._tokenizer.advance()
                self._assert_identifier(advance=False)
                name = ".".join([name, self._tokenizer.token])
                self._write(token_type="subroutine", token=name)
                self._assert_token("(")
                self._compile_expression_list()
                self._assert_token(")")
            else:
                self._write(token_type="var", token=name, advance=False)
                if self._check_token("["):
                    self._compile_expression()
                    self._assert_token("]")
        elif self._check_token("("):
            self._compile_expression()
            self._assert_token(")")
        elif self._check_token(_UNARY_OPS):
            self._compile_term()
        self._close_block("term")

    def _compile_expression_list(self):
        """
        Compile code of the form:
            (expression (',' expression)*)?
        """
        self._open_block("expressionList")
        if (self._tokenizer.token in _TYPE_TOKENS
                or self._tokenizer.token_type in _TYPE_TYPES):
            self._compile_expression()
            while self._check_token(","):
                self._compile_expression()
        self._close_block("expressionList")

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
    def _assert_token(self, token, advance=True):
        super()._assert_token(token)
        if advance:
            self._tokenizer.advance()

    def _assert_identifier(self, advance=True):
        super()._assert_identifier()
        if advance:
            self._tokenizer.advance()

    def _assert_type(self, advance=True):
        super()._assert_type()
        if advance:
            self._tokenizer.advance()

    def _assert_subroutine_type(self, advance=True):
        super()._assert_subroutine_type()
        if advance:
            self._tokenizer.advance()

    # ----------------------CHECKING FUNCTIONS-----------------------
    def _check_token(self, token, advance=True):
        if self._tokenizer.token in token:
            if advance:
                self._tokenizer.advance()
            return True
        return False

    # ------------------------OTHER FUNCTIONS------------------------
    def _define(self, type_, kind):
        name = self._get_assert(self._assert_identifier)
        self._symboltable.define(name, type_, kind)

    def _get_assert(self, assertion=None):
        val = self._tokenizer.token
        if assertion is None:
            self._tokenizer.advance()
        else:
            assertion()
        return val


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_UNARY_OPS = frozenset("-~")
_OPS = frozenset("+-*/&|<>=")
_TYPE_TOKENS = frozenset("(") | _UNARY_OPS | _KEYWORD_CONSTANTS
_TYPE_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
