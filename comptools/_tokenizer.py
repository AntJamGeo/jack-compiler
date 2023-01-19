from comptools._error import JackError


class JackTokenizer:
    """
    A tokenizer for the Jack language.

    Reads in a .jack file and identifies the individual tokens within
    the file, to be passed on for compilation into virtual machine
    language.

    Attributes
    ----------
    has_more_tokens : bool
        True until the end of the file is reached
    token : str
        The last token to have been identified
    token_type : str
        The type of the last token
    line_no : int
        The current line number

    Methods
    -------
    advance()
        Advances to the next token in the file.
    """
    def __init__(self, file, file_path):
        self._file = file
        self._file_path = file_path
        self._has_more_tokens = True
        self._token = None
        self._token_type = None
        self._line = ""
        self._line_no = 0
        self._char_no = 0

    def advance(self):
        """Advance to the next token in the file."""
        while self._has_more_tokens:
            if self._char_no == len(self._line):
                self._go_to_next_line()
            else:
                first = self._line[self._char_no]
                if first in _START_WORD_CHARS:
                    self._build_token(_WORD_CHARS)
                    self._token_type = (
                        "keyword" if self._token in _KEYWORDS
                        else "identifier")
                elif first in _SYMBOLS:
                    self._token = first
                    self._token_type = "symbol"
                    self._char_no += 1
                elif first in _DIGITS:
                    self._build_token(_DIGITS)
                    self._token_type = "integerConstant"
                elif first in _QUOTE:
                    self._char_no += 1
                    end_of_string = self._line.find("\"", self._char_no)
                    if end_of_string == -1:
                        raise JackError(
                            self._file_path,
                            f"Unclosed string on line {self._line_no}."
                        )
                    self._token = self._line[self._char_no:end_of_string]
                    self._token_type = "stringConstant"
                    self._char_no = end_of_string + 1
                elif first in _SPACE:
                    self._char_no += 1
                    continue
                elif first in _SLASH:
                    if self._is_comment():
                        continue
                else:
                    raise JackError(
                        self._file_path,
                        f"Invalid character \"{first}\" detected "
                        f"on line {self._line_no}.\nBad line: {self._line}"
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
            self._token = "/"
            self._token_type = "symbol"
            return False
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
                raise JackError(
                    self._file_path,
                    "Multi-line comment left unclosed. Are you "
                    "missing an */ somewhere?"
                )
        else:
            self._token = "/"
            self._token_type = "symbol"
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
            self._token = None
            self._token_type = None


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
    def line_no(self):
        return self._line_no


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
