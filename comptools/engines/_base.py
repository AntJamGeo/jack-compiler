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
                if self._tokenizer.has_more_tokens:
                    self._raise_error(
                        "Syntax",
                        "all code should be within a single class block"
                    )
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
    def _assert_has_more_tokens(self, prev=False):
        if not self._tokenizer.has_more_tokens:
            self._raise_error(
                "EndOfFile",
                "class block left unclosed",
                prev
            )

    def _assert_class_name_match(self):
        if self._class_name != self._tokenizer.token:
            self._raise_error("Class", "class name must match file name")

    def _assert_token(self, token, prev=False):
        self._assert_has_more_tokens()
        if self._tokenizer.token != token:
            self._raise_error(
                "Syntax",
                f"expected '{token}' but got '{self._tokenizer.token}'",
                prev
            )

    def _assert_identifier(self, prev=False):
        self._assert_has_more_tokens()
        if self._tokenizer.token_type != "identifier":
            self._raise_error(
                "Syntax",
                (
                    "expected an identifier but got a "
                    f"{self._tokenizer.token_type}"
                ),
                prev
            )

    def _assert_type(self, prev=False):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            self._raise_error(
                "Syntax",
                (
                    "expected a type keyword (int/char/boolean/<class name>) "
                    f"but got '{self._tokenizer.token}'"
                ),
                prev
            )

    def _assert_subroutine_type(self, prev=False):
        self._assert_has_more_tokens()
        if (self._tokenizer.token not in _SUBROUTINE_TYPE_KEYWORDS
                and self._tokenizer.token_type != "identifier"):
            self._raise_error(
                "Syntax",
                (
                    "expected a return type (void/int/char/boolean/"
                    f"<class name>) but got '{self._tokenizer.token}'"
                ),
                prev
            )

    # ------------------------ERROR FUNCTION-------------------------
    def _raise_error(self, err, info, prev=False):
        if prev:
            line_no = self._tokenizer.prev_start_line_no
            line = self._tokenizer.prev_start_line
            char_no = self._tokenizer.prev_start_char_no
        else:
            line_no = self._tokenizer.start_line_no
            line = self._tokenizer.start_line
            char_no = self._tokenizer.start_char_no
        raise JackError(
                self._class_name,
                line_no,
                line,
                char_no,
                err,
                info
                )

    def _raise_subroutine_call_error(self):
        self._raise_error(
            "Subroutine",
            "expected subroutine call",
            True
        )

    # ------------------------OTHER FUNCTIONS------------------------
    def _get_var(self, name, prev=False):
        var = self._symboltable.get_var(name)
        if var is None:
            self._raise_error(
                "Variable",
                f"variable '{name}' has not been declared",
                prev
            )
        return var


_TYPE_KEYWORDS = frozenset(("int", "char", "boolean"))
_SUBROUTINE_TYPE_KEYWORDS = frozenset(("void", "int", "char", "boolean"))
