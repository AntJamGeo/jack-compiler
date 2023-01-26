import os

from comptools._error import JackError
from comptools._tokenizer import JackTokenizer

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
                success = True
            except JackError as e:
                print(e.message)
                success = False
        if success:
            print(
                f"File '{self._tokenizer.file_name}' compiled to"
                f" '{self._writer.file_name}' successfully!"
            )
        else:
            os.remove(self._writer.file_name)
        return success

    def _compile_class(self):
        raise NotImplementedError("Engine requires a _compile_class method.")

    # ----------------------ASSERTION FUNCTIONS----------------------
    def _assert_has_more_tokens(self):
        if not self._tokenizer.has_more_tokens:
            self._raise_error(
                "Unexpected End of File",
                "Program seems unfinished. Have you missed something?"
            )

    def _assert_token(self, token):
        self._assert_has_more_tokens()
        if self._tokenizer.token != token:
            self._raise_error(
                "Token",
                f"Expected token '{token}' but got '{self._tokenizer.token}'."
            )

    def _assert_identifier(self):
        self._assert_has_more_tokens()
        if self._tokenizer.token_type != "identifier":
            self._raise_error(
                "Identifier",
                (
                    "Expected an identifier but got a "
                    f"{self._tokenizer.token_type}."
                )
            )

    def _assert_type(self):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            self._raise_error(
                "Syntax",
                "Expected a type keyword (int/char/boolean) or class name."
            )

    def _assert_subroutine_type(self):
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


_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
