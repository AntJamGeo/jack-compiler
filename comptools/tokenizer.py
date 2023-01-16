import sys


class JackTokenizer:
    def __init__(self, file_path):
        self._file_path = file_path
        self._file = None
        self._has_more_tokens = None
        self._token = None
        self._token_type = None
        self._line = None
        self._line_no = None
        self._char_no = None

    def __enter__(self):
        self._file = open(self._file_path, "r")
        self._has_more_tokens = True
        self._line = ""
        self._line_no = 0
        self._char_no = 0
        self.advance()
        return self

    def __exit__(self, *args):
        self._file.close()

    def advance(self):
        while self._has_more_tokens:
            if self._char_no == len(self._line):
                self._go_to_next_line()
            else:
                first = self._line[self._char_no]
                if first in _START_WORD_CHARS:
                    self._build_token(_WORD_CHARS)
                    self._token_type = (
                        "KEYWORD" if self._token in _KEYWORDS
                        else "IDENTIFIER")
                elif first in _SYMBOLS:
                    self._token = first
                    self._token_type = "SYMBOL"
                    self._char_no += 1
                elif first in _DIGITS:
                    self._build_token(_DIGITS)
                    self._token_type = "INT_CONST"
                elif first in _QUOTE:
                    self._char_no += 1
                    end_of_string = self._line.find("\"", self._char_no)
                    if end_of_string == -1:
                        self._error(
                            f"Unclosed string in file '{self._file_path}' "
                            f"on line {self._line_no}"
                        )
                    self._token = self._line[self._char_no:end_of_string]
                    self._token_type = "STRING_CONST"
                    self._char_no = end_of_string + 1
                elif first in _SPACE:
                    self._char_no += 1
                    continue
                elif first in _SLASH:
                    if self._is_comment():
                        continue
                else:
                    self._error(
                        f"Invalid character \"{first}\" detected in file "
                        f"'{self._file_path}' on line {self._line_no}.\nBad "
                        f"line : {self._line}"
                    )
                return

    def _build_token(self, valid_chars):
        start = self._char_no
        while (self._char_no < len(self._line)
                and self._line[self._char_no] in valid_chars):
            self._char_no += 1
        self._token = self._line[start:self._char_no]

    def _is_comment(self):
        self._char_no += 1
        if self._char_no == len(self._line):
            return
        cur = self._line[self._char_no]
        if cur in _SLASH:
            self._go_to_next_line()
        elif cur in _ASTERISK:
            while self._has_more_tokens:
                end_of_comment_index = self._line.find("*/", self._char_no)
                if end_of_comment_index == -1:
                    self._go_to_next_line()
                    continue
                else:
                    self._char_no = end_of_comment_index + 2
                    break
            else:
                self._error(
                    "Multi-line comment left unclosed. Are you "
                    "missing an */ somewhere?"
                )
        else:
            self._token = "/"
            self._token_type = "SYMBOL"
            return False
        return True

    def _go_to_next_line(self):
        self._line_no += 1
        self._line = self._file.readline()
        self._char_no = 0
        if self._line:
            self._line = self._line.strip()
        else:
            self._has_more_tokens = False

    def _error(self, message):
        print(message)
        sys.exit(1)

    @property
    def has_more_tokens(self):
        return self._has_more_tokens

    @property
    def token(self):
        return self._token

    @property
    def token_type(self):
        return self._token_type

    @property
    def line(self):
        return self._line

_START_WORD_CHARS = frozenset(
        "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM_")
_SYMBOLS = frozenset("{}()[].,;+-*&|<>=~")
_DIGITS = frozenset("1234567890")
_QUOTE = frozenset("\"")
_WORD_CHARS = _START_WORD_CHARS | _DIGITS
_SPACE = frozenset(" ")
_SLASH = frozenset("/")
_ASTERISK = frozenset("*")

_KEYWORDS = frozenset((
        "class", "constructor", "function", "method", "field", "static",
        "var", "int", "char", "boolean", "void", "true", "false", "null",
        "this", "let", "do", "if", "else", "while", "return"))
