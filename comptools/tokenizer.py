class JackTokenizer:
    def __init__(self, file_path):
        self._file_path = file_path
        self._file = None
        self._has_more_tokens = None
        self._token = None
        self._line = None

    def __entry__(self):
        self._file = open(self._file_path, "r")
        self._has_more_tokens = True
        self._line = 0
        self.advance()
        return self

    def __exit__(self, *args):
        self._file.close()

    def advance(self):
        pass

    @property
    def has_more_tokens(self):
        return self._has_more_tokens

    @property
    def token(self):
        return self._token
