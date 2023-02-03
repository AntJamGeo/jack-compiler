import os

from comptools.engines._base import CompilationEngine
from comptools._writers import XMLWriter
from comptools._symboltable import SymbolTable


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
        self._symboltable = SymbolTable()
        self._open_block("class")
        self._write_token("class")
        self._assert_class_name_match()
        self._write_identifier("class")
        self._write_token("{")
        self._compile_class_var_dec()
        self._compile_subroutine()
        self._write_token("}")
        self._close_block("class")

    def _compile_class_var_dec(self):
        """
        Compiles code of the form:
            ('static' | 'field') type varName (',' varName)* ';'
        """
        while self._tokenizer.token in _CLASS_VAR_DEC_KEYWORDS:
            kind = self._tokenizer.token
            if kind == "field":
                kind = "this"
            self._open_block("classVarDec")
            self._write()
            type_ = self._tokenizer.token
            self._write_type()
            self._write_var(type_, kind)
            while self._check_token(","):
                self._write_var(type_, kind)
            self._write_token(";")
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
            self._write_subroutine_type()
            self._write_identifier(subroutine_category)
            self._write_token("(")
            self._compile_parameter_list()
            self._write_token(")")
            # subroutineBody of form:
                # '{' varDec* statements '}'
            self._open_block("subroutineBody")
            self._write_token("{")
            self._compile_var_dec()
            self._compile_statements()
            self._write_token("}")
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
            type_ = self._tokenizer.token
            self._write()
            self._write_var(type_, "argument")
            while self._check_token(","):
                type_ = self._tokenizer.token
                self._write_type()
                self._write_var(type_, "argument")
        self._close_block("parameterList")

    def _compile_var_dec(self):
        """
        Compiles code of the form:
            'var' type varName (',' varName)* ';'
        """

        while self._tokenizer.token == "var":
            self._open_block("varDec")
            self._write()
            type_ = self._tokenizer.token
            self._write_type()
            self._write_var(type_, "local")
            while self._check_token(","):
                self._write_var(type_, "local")
            self._write_token(";")
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
        self._write_var(define=False)
        if self._check_token("["):
            self._compile_expression()
            self._write_token("]")
        self._write_token("=")
        self._compile_expression()
        self._write_token(";")
        self._close_block("letStatement")

    def _compile_if(self):
        """
        Compile code of the form:
            'if' '(' expression ')' '{' statements '}'
            ('else' '{' statements '}')?
        """
        self._open_block("ifStatement")
        self._write()
        self._write_token("(")
        self._compile_expression()
        self._write_token(")")
        self._write_token("{")
        self._compile_statements()
        self._write_token("}")
        if self._check_token("else"):
            self._write_token("{")
            self._compile_statements()
            self._write_token("}")
        self._close_block("ifStatement")

    def _compile_while(self):
        """
        Compile code of the form:
            'while' '(' expression ')' '{' statements '}'
        """
        self._open_block("whileStatement")
        self._write()
        self._write_token("(")
        self._compile_expression()
        self._write_token(")")
        self._write_token("{")
        self._compile_statements()
        self._write_token("}")
        self._close_block("whileStatement")

    def _compile_do(self):
        """
        Compile code of the form:
            'do' subroutineCall ';'
        """
        self._open_block("doStatement")
        self._write()
        self._assert_identifier()
        name = self._tokenizer.token
        self._tokenizer.advance()
        self._compile_subroutine_call(name, True)
        self._write_token(";")
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
        self._write_token(";")
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
            self._assert_identifier()
            name = self._tokenizer.token
            self._tokenizer.advance()
            if self._compile_subroutine_call(name, assertion=False):
                pass
            elif self._check_token("["):
                self._compile_expression()
                self._write_token("]")
            else:
                var = self._get_var(name, prev=True)
                self._write(
                    f"{var['kind']}.{var['type']}.{var['index']}", name, False)
        elif self._check_token("("):
            self._compile_expression()
            self._write_token(")")
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

    def _compile_subroutine_call(self, name, assertion):
        """
        Compilie code of the form
            ((className | varName) '.')?
            subroutineName '(' expressionList ')'
        """
        local_method = True
        if self._check_token(".", write=False):
            self._tokenizer.advance()
            self._assert_identifier()
            subroutine = self._tokenizer.token
            var = self._symboltable.get_var(name)
            if var is None:
                self._write("class", name, False)
            else:
                self._write(
                    f"{var['kind']}.{var['type']}.{var['index']}", name, False)
            self._write("symbol", ".", False)
            self._write("subroutine", subroutine, True)
            local_method = False
        if self._check_token("(", write=False):
            if local_method:
                self._write("subroutine", name, False)
            self._write_token("(")
            self._compile_expression_list()
            self._write_token(")")
            return True
        elif assertion:
            self._raise_subroutine_call_error()
        return False

    # -----------------------WRITING FUNCTIONS-----------------------
    def _write(self, token_type=None, token=None, advance=True):
        if token_type is None:
            token_type = self._tokenizer.token_type
        if token is None:
            token = self._tokenizer.token
        self._writer.write(token_type, token)
        if advance:
            self._tokenizer.advance()

    def _write_token(self, token):
        super()._assert_token(token)
        self._write()

    def _write_identifier(self, category=None):
        super()._assert_identifier()
        self._write(token_type=category)

    def _write_type(self):
        super()._assert_type()
        self._write()

    def _write_subroutine_type(self):
        super()._assert_subroutine_type()
        self._write()

    def _write_var(self, type_=None, kind=None, define=True):
        if define:
            self._define(type_, kind)
        var = self._get_var(self._tokenizer.token)
        self._write_identifier(f"{var['kind']}.{var['type']}.{var['index']}")

    def _open_block(self, block):
        self._writer.open_block(block)

    def _close_block(self, block):
        self._writer.close_block(block)

    # ----------------------CHECKING FUNCTIONS-----------------------
    def _check_token(self, token, write=True):
        if self._tokenizer.token in token:
            if write:
                self._write()
            return True
        return False

    # ------------------------OTHER FUNCTIONS------------------------
    def _define(self, type_, kind, name=None):
        if name is None:
            name = self._tokenizer.token
        self._symboltable.define(name, type_, kind)


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_UNARY_OPS = frozenset("-~")
_OPS = frozenset("+-*/&|<>=")
_TYPE_TOKENS = frozenset("(") | _UNARY_OPS | _KEYWORD_CONSTANTS
_TYPE_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
