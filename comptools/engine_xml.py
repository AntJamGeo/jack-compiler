import os

from comptools._error import JackError
from comptools._tokenizer import JackTokenizer


class CompilationEngineVM:
    def __init__(self, in_path):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def run(self):
        return True, ""

class CompilationEngineXML:
    """
    Compile a .jack file.

    Methods
    -------
    run()
        Compile the provided .jack file provided on initialisation.
    """
    def __init__(self, in_path):
        self._class_name = os.path.splitext(in_path)[0]
        self._in_path = in_path
        self._out_path = self._class_name + ".xml"
        self._in_file = None
        self._out_file = None
        self._tokenizer = None
        self._indent = ''

    def __enter__(self):
        self._in_file = open(self._in_path, "r")
        self._out_file = open(self._out_path, "w")
        self._tokenizer = JackTokenizer(self._in_file, self._class_name)
        return self

    def __exit__(self, *args):
        self._in_file.close()
        self._out_file.close()

    def run(self):
        """
        Compile the provided .jack file provided on initialisation.

        Returns
        -------
        bool
            On successful compilation, returns True, while returns
            False on encountering an error.
        self._out_path
            The location of the output file.
        """
        try:
            self._tokenizer.advance()
            if self._tokenizer.has_more_tokens:
                self._compile_class()
            return True, self._out_path
        except JackError as e:
            print(e.message)
            return False, self._out_path

    # ---------------------COMPILATION FUNCTIONS---------------------
    def _compile_class(self):
        """
        Compiles code of the form:
            'class' className '{' classVarDec* subroutineDec* '}'
        """
        self._open_block("class")
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
    def _write(self, token_type=None, token=None, advance=True):
        if token_type is None:
            token_type = self._tokenizer.token_type
        if token is None:
            token = self._tokenizer.token
        self._out_file.write(
            f"{self._indent}<{token_type}> "
            f"{_XML_MAP.get(token, token)} "
            f"</{token_type}>\n"
        )
        if advance:
            self._tokenizer.advance()

    def _open_block(self, block):
        self._out_file.write(f"{self._indent}<{block}>\n")
        self._indent += ' ' * _INDENT_SPACES

    def _close_block(self, block):
        self._indent = self._indent[:-_INDENT_SPACES]
        self._out_file.write(f"{self._indent}</{block}>\n")

    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_has_more_tokens(self):
        if not self._tokenizer.has_more_tokens:
            self._raise_error(
                "Unexpected End of File",
                "Program seems unfinished. Have you missed something?"
            )

    def _assert_token(self, token, write=True):
        self._assert_has_more_tokens()
        if self._tokenizer.token != token:
            self._raise_error(
                "Token",
                f"Expected token '{token}' but got '{self._tokenizer.token}'."
            )
        if write:
            self._write()

    def _assert_identifier(self, category=None, write=True):
        self._assert_has_more_tokens()
        if self._tokenizer.token_type != "identifier":
            self._raise_error(
                "Identifier",
                (
                    "Expected an identifier but got a "
                    f"{self._tokenizer.token_type}."
                )
            )
        if write:
            self._write(token_type=category)

    def _assert_type(self, write=True):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            self._raise_error(
                "Syntax",
                "Expected a type keyword (int/char/boolean) or class name."
            )
        if write:
            self._write()

    def _assert_subroutine_type(self, write=True):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _SUBROUTINE_TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            self._raise_error(
                "Syntax",
                (
                    "Expected a return type (void/int/char/boolean/"
                    f"<class name>) but got '{self._tokenizer.token}'."
                )
            )
        if write:
            self._write()

    # ----------------------CHECKING FUNCTIONS-----------------------
    def _check_token(self, token, write=True):
        if self._tokenizer.token in token:
            if write:
                self._write()
            return True
        return False

    # ------------------------ERROR FUNCTION-------------------------
    def _raise_error(self, type_="Syntax", info=None):
        raise JackError(
                self._class_name,
                self._tokenizer.start_line_no,
                self._tokenizer.start_line,
                self._tokenizer.start_char_no,
                type_,
                info
                )


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_UNARY_OPS = frozenset("-~")
_OPS = frozenset("+-*/&|<>=")
_TYPE_TOKENS = frozenset("(") | _UNARY_OPS | _KEYWORD_CONSTANTS
_TYPE_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
_INDENT_SPACES = 2
_XML_MAP = {"<": "&lt;", ">": "&gt;", "'": "&quot;", "&": "&amp;"}
