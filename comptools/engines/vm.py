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
        self._close_block("class")
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
            var_category = self._tokenizer.token
            self._open_block("classVarDec")
            self._write()
            self._assert_type()
            self._assert_identifier(var_category)
            while self._check_token(","):
                self._assert_identifier(var_category)
            self._assert_token(";")
            self._close_block("classVarDec")

    def _compile_subroutine(self):
        """
        Compiles code of the form:
            ('constructor' | 'function' | 'method') ('void' | type)
            subroutineName '(' parameterList ')' subroutineBody
        """
        while self._tokenizer.token in _SUBROUTINE_DEC_KEYWORDS:
            subroutine_category = self._tokenizer.token
            self._open_block("subroutineDec")
            self._write()
            self._assert_subroutine_type()
            self._assert_identifier(subroutine_category)
            self._assert_token("(")
            self._compile_parameter_list()
            self._assert_token(")")
            # subroutineBody of form:
                # '{' varDec* statements '}'
            self._open_block("subroutineBody")
            self._assert_token("{")
            self._compile_var_dec()
            self._compile_statements()
            self._assert_token("}")
            self._close_block("subroutineBody")
            self._close_block("subroutineDec")

    def _compile_parameter_list(self):
        """
        Compiles code of the form:
            ( (type varName) (',' type varName)*)?
        """

        self._open_block("parameterList")
        if (self._tokenizer.token in _TYPE_KEYWORDS
                or self._tokenizer.token_type == "identifier"):
            self._write()
            self._assert_identifier("argument")
            while self._check_token(","):
                self._assert_type()
                self._assert_identifier("argument")
        self._close_block("parameterList")

    def _compile_var_dec(self):
        """
        Compiles code of the form:
            'var' type varName (',' varName)* ';'
        """

        while self._tokenizer.token == "var":
            self._open_block("varDec")
            self._write()
            self._assert_type()
            self._assert_identifier("var")
            while self._check_token(","):
                self._assert_identifier("var")
            self._assert_token(";")
            self._close_block("varDec")

    def _compile_statements(self):
        """
        Compiles a series of statements, which must begin with the
        keywords: 'let', 'if', 'while', 'do', or 'return'.
        """
        self._open_block("statements")
        while True:
            if self._tokenizer.token == "let":
                self._compile_let()
            elif self._tokenizer.token == "if":
                self._compile_if()
            elif self._tokenizer.token == "while":
                self._compile_while()
            elif self._tokenizer.token == "do":
                self._compile_do()
            elif self._tokenizer.token == "return":
                self._compile_return()
            else:
                self._close_block("statements")
                return

    def _compile_let(self):
        """
        Compile code of the form:
            'let' varName ('[' expression ']')? '=' expression ';'
        """
        self._open_block("letStatement")
        self._write()
        self._assert_identifier("var")
        if self._check_token("["):
            self._compile_expression()
            self._assert_token("]")
        self._assert_token("=")
        self._compile_expression()
        self._assert_token(";")
        self._close_block("letStatement")

    def _compile_if(self):
        """
        Compile code of the form:
            'if' '(' expression ')' '{' statements '}'
            ('else' '{' statements '}')?
        """
        self._open_block("ifStatement")
        self._write()
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
        self._close_block("ifStatement")

    def _compile_while(self):
        """
        Compile code of the form:
            'while' '(' expression ')' '{' statements '}'
        """
        self._open_block("whileStatement")
        self._write()
        self._assert_token("(")
        self._compile_expression()
        self._assert_token(")")
        self._assert_token("{")
        self._compile_statements()
        self._assert_token("}")
        self._close_block("whileStatement")

    def _compile_do(self):
        """
        Compile code of the form:
            'do' subroutineCall ';'
        """
        self._open_block("doStatement")
        self._write()
        # subroutineCall of form:
            # ((className | varName) '.')?
            # subroutineName '(' expressionList ')'
        self._assert_identifier(write=False)
        subroutine = self._tokenizer.token
        self._tokenizer.advance()
        if self._check_token(".", write=False):
            self._tokenizer.advance()
            self._assert_identifier(write=False)
            subroutine = ".".join([subroutine, self._tokenizer.token])
            self._tokenizer.advance()
        self._write(token_type="subroutine", token=subroutine, advance=False)
        self._assert_token("(")
        self._compile_expression_list()
        self._assert_token(")")
        self._assert_token(";")
        self._close_block("doStatement")

    def _compile_return(self):
        """
        Compile code of the form:
            'return' expression? ';'
        """
        self._open_block("returnStatement")
        self._write()
        if self._tokenizer.token != ";":
            self._compile_expression()
        self._assert_token(";")
        self._close_block("returnStatement")

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
            if self._check_token(".", write=False):
                self._tokenizer.advance()
                self._assert_identifier(write=False)
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
    def _write(self, advance=True, **kwargs):
        if advance:
            self._tokenizer.advance()

    def _open_block(self, block):
        pass

    def _close_block(self, block):
        pass

    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_token(self, token, write=True):
        super()._assert_token(token)
        if write:
            self._tokenizer.advance()

    def _assert_identifier(self, category=None, write=True):
        super()._assert_identifier()
        if write:
            self._tokenizer.advance()

    def _assert_type(self, write=True):
        super()._assert_type()
        if write:
            self._tokenizer.advance()

    def _assert_subroutine_type(self, write=True):
        super()._assert_subroutine_type()
        if write:
            self._tokenizer.advance()

    # ----------------------CHECKING FUNCTIONS-----------------------
    def _check_token(self, token, write=True):
        if self._tokenizer.token in token:
            if write:
                self._write()
            return True
        return False


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_UNARY_OPS = frozenset("-~")
_OPS = frozenset("+-*/&|<>=")
_TYPE_TOKENS = frozenset("(") | _UNARY_OPS | _KEYWORD_CONSTANTS
_TYPE_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
