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
        self._indentation = 0

    def __enter__(self):
        out_path = os.path.splitext(self._file_path)[0] + ".xml"
        self._in_file = open(self._file_path, "r")
        self._out_file = open(out_path, "w")
        self._tokenizer = JackTokenizer(self._in_file, self._file_path)
        return self

    def __exit__(self, *args):
        self._in_file.close()
        self._out_file.close()

    def _write_terminal(self):
        self._out_file.write(
                f"{' ' * self._indentation}"
                f"<{self._tokenizer.token_type}> "
                f"{self._tokenizer.token} "
                f"</{self._tokenizer.token_type}>\n")

    def _write_non_terminal(self, string):
        self._out_file.write(string)

    def _assert_token(self, token):
        self._tokenizer.advance()
        if (not self._tokenizer.has_more_tokens
                or self._tokenizer.token != token):
            error(
                f"Error in module {self._file_path} on line "
                f"{self._tokenizer.line_no}.\n"
                f"Expected token '{token}' but got '{self._tokenizer.token}'."
            )
        self._write_terminal()

    def _assert_type(self, type_):
        self._tokenizer.advance()
        if (not self._tokenizer.has_more_tokens
                or self._tokenizer.token_type != type_):
            error(
                f"Error in module {self._file_path} on line "
                f"{self._tokenizer.line_no}.\n"
                f"Expected token type '{type_}' but got "
                f"'{self._tokenizer.token}' which is a "
                f"'{self._tokenizer.token_type}'."
            )
        self._write_terminal()

    def compile_class(self):
        """
        Compile the provided .jack file provided on initialisation.
        """
        spaces = ' ' * self._indentation
        self._indentation += 2
        self._write_non_terminal(f"{spaces}<class>\n")
        self._assert_token("class")
        self._assert_type("identifier")
        self._assert_token("{")
        self._compile_class_var_dec()
        self._compile_subroutine()
        self._assert_token("}")
        self._write_non_terminal(f"{spaces}</class>\n")
        self._tokenizer.advance()
        if self._tokenizer.has_more_tokens:
            error(
                "All code should be within a single class block."
                f"There exists code outside this in module {self._file_path}"
                f" on line {self._tokenizer.line_no}."
            )

    def _compile_class_var_dec(self):
        pass

    def _compile_subroutine(self):
        pass

