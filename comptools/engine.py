import os

from comptools._error import error
from comptools.tokenizer import JackTokenizer


class CompilationEngine:
    """
    Compile a .jack file.

    Methods
    -------
    compile_class()
        Compile the provided .jack file provided on initialisation.
    """
    def __init__(self, file_path):
        self._file_path = file_path
        self._in_file = None
        self._out_file = None
        self._tokenizer = None
        self._indent = ''

    def __enter__(self):
        out_path = os.path.splitext(self._file_path)[0] + ".xml"
        self._in_file = open(self._file_path, "r")
        self._out_file = open(out_path, "w")
        self._tokenizer = JackTokenizer(self._in_file, self._file_path)
        return self

    def __exit__(self, *args):
        self._in_file.close()
        self._out_file.close()

    # ---------------------COMPILATION FUNCTIONS---------------------
    def compile_class(self):
        self._tokenizer.advance()
        self._open_block("class")
        self._assert_token("class")
        self._write_terminal()

        self._assert_token_type("identifier")
        self._write_terminal()

        self._assert_token("{")
        self._write_terminal()

        self._compile_class_var_dec()

        self._compile_subroutine()

        self._assert_token("}")
        self._write_terminal()

        self._close_block("class")

        if self._tokenizer.has_more_tokens:
            error(
                self._file_path,
                "All code should be within a single class block."
                f"There exists code outside of this"
                f" on line {self._tokenizer.line_no}."
            )

    def _compile_class_var_dec(self):
        while self._tokenizer.token in _CLASS_VAR_DEC_KEYWORDS:
            self._open_block("classVarDec")
            self._write_terminal()

            self._assert_type()
            self._write_terminal()

            self._assert_token_type("identifier")
            self._write_terminal()

            while self._tokenizer.token == ",":
                self._write_terminal()

                self._assert_token_type("identifier")
                self._write_terminal()

            self._assert_token(";")
            self._write_terminal()

            self._close_block("classVarDec")

    def _compile_subroutine(self):
        pass

    def _compile_parameter_list(self):
        pass

    def _compile_var_dec(self):
        pass

    def _compile_statements(self):
        pass

    def _compile_let(self):
        pass

    def _compile_if(self):
        pass

    def _compile_while(self):
        pass

    def _compile_do(self):
        pass

    def _compile_return(self):
        pass

    def _compile_expression(self):
        pass

    def _compile_term(self):
        pass

    def _compile_expression_list(self):
        pass

    # -----------------------WRITING FUNCTIONS-----------------------
    def _write_terminal(self):
        self._out_file.write(
            f"{self._indent}<{self._tokenizer.token_type}> "
            f"{self._tokenizer.token} </{self._tokenizer.token_type}>\n"
        )
        self._tokenizer.advance()

    def _open_block(self, block):
        self._out_file.write(f"{self._indent}<{block}>\n")
        self._indent += ' ' * _INDENT_SPACES

    def _close_block(self, block):
        self._indent = self._indent[:-_INDENT_SPACES]
        self._out_file.write(f"{self._indent}</{block}>\n")

    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_has_more_tokens(self):
        if not self._tokenizer._has_more_tokens:
            error(
                self._file_path,
                "Program seems unfinished. Have you missed something?"
            )

    def _assert_token(self, token):
        self._assert_has_more_tokens()
        if self._tokenizer.token != token:
            error(
                self._file_path,
                f"On line {self._tokenizer.line_no}, "
                f"expected token '{token}' but got '{self._tokenizer.token}'."
            )

    def _assert_token_type(self, type_):
        self._assert_has_more_tokens()
        if self._tokenizer.token_type != type_:
            error(
                self._file_path,
                f"On line {self._tokenizer.line_no}, "
                f"expected token type '{type_}' but got "
                f"'{self._tokenizer.token}' which is a "
                f"'{self._tokenizer.token_type}'."
            )

    def _assert_type(self):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            error(
                self._file_path,
                f"On line {self._tokenizer.line_no}, "
                "expected a type (int, char, boolean, or class name) but got "
                f"'{self._tokenizer.token}'."
            )


_INDENT_SPACES = 2
_CLASS_VAR_DEC_KEYWORDS = frozenset(("static", "field"))
_SUBROUTINE_DEC_KEYWORDS = frozenset(("constructor", "function", "method"))
_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
