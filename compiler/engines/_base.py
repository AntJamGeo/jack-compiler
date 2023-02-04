import os

from _error import JackError
from _tokenizer import JackTokenizer
from _symboltable import SymbolTable

class CompilationEngine:
    def __init__(self, writer):
        self._tokenizer = JackTokenizer()
        self._writer = writer

    def run(self, class_name):
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
        self._class_name = class_name
        self._tokenizer.load_class(class_name)
        self._writer.load_class(class_name)
        with self._tokenizer, self._writer:
            try:
                self._tokenizer.advance()
                if self._tokenizer.has_more_tokens:
                    self._compile_class()
                if self._tokenizer.has_more_tokens:
                    self._raise_error(
                        "Syntax",
                        "all code should be within a single class block"
                    )
                print(
                    f"File '{self._tokenizer.file_name}' compiled to"
                    f" '{self._writer.file_name}' successfully!"
                )
                success = True
            except JackError as e:
                print(e.message)
                os.remove(self._writer.file_name)
                success = False
        return success

    def _compile_class(self):
        """
        Compiles code of the form:
            'class' className '{' classVarDec* subroutineDec* '}'
        """
        self._symboltable = SymbolTable()
        self._absorb("class")
        self._absorb(":class_name")
        self._absorb("{")
        while self._tokenizer.token in _CLASS_VAR_DEC_KEYWORDS:
            self._compile_class_var_dec()
        while self._tokenizer.token in _SUBROUTINE_DEC_KEYWORDS:
            self._compile_subroutine()
        self._absorb("}")

    def _compile_class_var_dec(self):
        """
        Compiles code of the form:
            ('static' | 'field') type varName (',' varName)* ';'
        """
        kind = self._absorb()
        if kind == "field":
            kind = "this"
        type_ = self._absorb(":var_type")
        self._symboltable.define(self._tokenizer.token, type_, kind)
        self._absorb(":var_dec")
        while self._tokenizer.token == ",":
            self._absorb()
            self._symboltable.define(self._tokenizer.token, type_, kind)
            self._absorb(":var_dec")
        self._absorb(";")

    def _compile_parameter_list(self):
        """
        Compiles code of the form:
            ( (type varName) (',' type varName)*)?
        """
        if self._is_var_type():
            type_ = self._absorb()
            self._symboltable.define(self._tokenizer.token, type_, "argument")
            self._absorb(":var_dec")
            while self._tokenizer.token == ",":
                self._absorb()
                type_ = self._absorb(":var_type")
                self._symboltable.define(self._tokenizer.token, type_, "argument")
                self._absorb(":var_dec")

    def _compile_var_dec(self):
        """
        Compiles code of the form:
            'var' type varName (',' varName)* ';'
        """
        self._absorb()
        type_ = self._absorb(":var_type")
        self._symboltable.define(self._tokenizer.token, type_, "local")
        self._absorb(":var_dec")
        while self._tokenizer.token == ",":
            self._absorb()
            self._symboltable.define(self._tokenizer.token, type_, "local")
            self._absorb(":var_dec")
        self._absorb(";")

    def _compile_statements(self):
        """
        Compiles a series of statements, which must begin with the
        keywords: 'let', 'if', 'while', 'do', or 'return'.
        """
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
                break

    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_has_more_tokens(self):
        if not self._tokenizer.has_more_tokens:
            self._raise_error("EndOfFile", "class block left unclosed")

    def _assert_class_name(self):
        if self._class_name != self._tokenizer.token:
            self._raise_error("Class", "class name must match file name")

    def _assert_token(self, token):
        self._assert_has_more_tokens()
        if self._tokenizer.token != token:
            self._raise_error(
                "Syntax",
                f"expected '{token}' but got '{self._tokenizer.token}'"
            )

    def _assert_identifier(self):
        self._assert_has_more_tokens()
        if self._tokenizer.token_type != "identifier":
            self._raise_error(
                "Syntax",
                (
                    "expected an identifier but got a "
                    f"{self._tokenizer.token_type}"
                )
            )

    def _assert_var_type(self):
        self._assert_has_more_tokens()
        if not self._is_var_type():
            self._raise_error(
                "Syntax",
                (
                    "expected a type keyword (int/char/boolean/<class name>) "
                    f"but got '{self._tokenizer.token}'"
                )
            )

    def _assert_subroutine_type(self):
        self._assert_has_more_tokens()
        if not self._is_subroutine_type():
            self._raise_error(
                "Syntax",
                (
                    "expected a return type (void/int/char/boolean/"
                    f"<class name>) but got '{self._tokenizer.token}'"
                )
            )

    # ------------------------ERROR FUNCTIONS------------------------
    def _raise_error(self, err, info, state=None):
        if state is None:
            line_no = self._tokenizer.start_line_no
            line = self._tokenizer.start_line
            char_no = self._tokenizer.start_char_no
        else:
            line_no = state.line_no
            line = state.line
            char_no = state.char_no
        raise JackError(
            self._class_name,
            line_no,
            line,
            char_no,
            err,
            info
        )

    def _raise_array_error(self, state=None):
        var = self._tokenizer.token if state is None else state.token
        self._raise_error("Array", f"'{var}' is not an array", state)

    def _raise_subroutine_error(self, state=None):
        self._raise_error("Subroutine", "expected subroutine call", state)

    def _raise_var_error(self, state=None):
        var = self._tokenizer.token if state is None else state.token
        self._raise_error("Variable", f"undeclared variable '{var}'", state)

    # ------------------------OTHER FUNCTIONS------------------------
    def _absorb(self, mode=None):
        if mode is not None:
            if mode == ":identifier" or mode == ":var_dec":
                self._assert_identifier()
            elif mode == ":var_type":
                self._assert_var_type()
            elif mode == ":subroutine_type":
                self._assert_subroutine_type()
            elif mode == ":class_name":
                self._assert_class_name()
            else:
                self._assert_token(mode)
        val = self._tokenizer.token
        self._tokenizer.advance()
        return val

    def _is_var_type(self):
        return (self._tokenizer.token in _VAR_TYPES
                or self._tokenizer.token_type == "identifier")

    def _is_subroutine_type(self):
        return (self._tokenizer.token in _SUBROUTINE_TYPES
                or self._tokenizer.token_type == "identifier")

    def _is_term(self):
        return (self._tokenizer.token in _TERM_TOKENS
                or self._tokenizer.token_type in _TERM_TYPES)

    def _is_binary_op(self):
        return self._tokenizer.token in _BINARY_OPS

    def _is_keyword_constant(self):
        return self._tokenizer.token in _KEYWORD_CONSTANTS

    def _is_unary_op(self):
        return self._tokenizer.token in _UNARY_OPS


_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_VAR_TYPES = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPES = frozenset(("void", "int", "char", "boolean"))
_TERM_TOKENS = frozenset(("(", "-", "~", "true", "false", "null", "this"))
_TERM_TYPES = frozenset(("integerConstant", "stringConstant", "identifier"))
_BINARY_OPS = frozenset("+-*/&|<>=")
_KEYWORD_CONSTANTS = frozenset(("true", "false", "null", "this"))
_UNARY_OPS = frozenset("-~")

