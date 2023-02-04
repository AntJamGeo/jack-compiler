from comptools._error import JackError


class JackTokenizer:
    """
    A tokenizer for the Jack language.

    Reads in a .jack file and identifies the individual tokens within
    the file, to be passed on for compilation

    Attributes
    ----------
    has_more_tokens : bool
        True until the end of the file is reached
    token : str
        The last token to have been identified
    token_type : str
        The type of the last token
    start_line : str
        The start line of the current token
    start_line_no : int
        The start line number of the current token
    start_char_no : int
        The start char number of the current token
    state : State
        The current state of the tokenizer

    Methods
    -------
    advance()
        Advances to the next token in the file.
    """
    def __init__(self):
        self._reset()

    def _reset(self):
        self._class_name = None
        self.file_name = None
        self._file = None
        self._has_more_tokens = True
        self._token = None
        self._token_type = None
        self._line = ""
        self._line_no = 0
        self._char_no = 0
        self._start_line = ""
        self._start_line_no = 0
        self._start_char_no = 0

    def load_class(self, class_name):
        self._reset()
        self._class_name = class_name
        self.file_name = class_name + ".jack"

    def __enter__(self):
        self._file = open(self.file_name, "r")
        return self

    def __exit__(self, *args):
        self._file.close()

    def advance(self):
        """Advance to the next token in the file."""
        while self._has_more_tokens:
            if self._char_no == len(self._line):
                self._go_to_next_line()
            else:
                first = self._line[self._char_no]
                if first in _SPACE:
                    self._char_no += 1
                    continue
                self._start_line = self._line
                self._start_line_no = self._line_no
                self._start_char_no = self._char_no
                if first in _SLASH:
                    if self._is_comment():
                        continue
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
                        self._raise_error("EndOfFile", "unclosed string")
                    self._token = self._line[self._char_no:end_of_string]
                    self._token_type = "stringConstant"
                    self._char_no = end_of_string + 1
                else:
                    self._raise_error("Syntax", "unidentified character")
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
                self._raise_error("EndOfFile", "unclosed multiline comment")
        else:
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

    def _raise_error(self, err, info):
        raise JackError(
                self._class_name,
                self._start_line_no,
                self._start_line,
                self._start_char_no,
                err,
                info
                )

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
    def start_line(self):
        return self._start_line

    @property
    def start_line_no(self):
        return self._start_line_no

    @property
    def start_char_no(self):
        return self._start_char_no

    @property
    def state(self):
        return State(
            self._token,
            self._token_type,
            self._start_line,
            self._start_line_no,
            self._start_char_no
        )


class State:
    def __init__(self, token, token_type, line, line_no, char_no):
        self.token = token
        self.token_type = token_type
        self.line = line
        self.line_no = line_no
        self.char_no = char_no


_START_WORD_CHARS = frozenset(
        "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM_")
_SYMBOLS = frozenset("{}()[].,;+-*/&|<>=~")
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
