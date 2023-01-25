from comptools._writer._base import Writer


class XMLWriter(Writer):
    def __init__(self, file):
        super().__init__(file)
        self._indent = ''

    def write(self, token_type, token):
        self._file.write(
            f"{self._indent}<{token_type}> "
            f"{_XML_MAP.get(token, token)} "
            f"</{token_type}>\n"
        )

    def open_block(self, block):
        self._file.write(f"{self._indent}<{block}>\n")
        self._indent += ' ' * _INDENT_SPACES

    def close_block(self, block):
        self._indent = self._indent[:-_INDENT_SPACES]
        self._file.write(f"{self._indent}</{block}>\n")


_INDENT_SPACES = 2
_XML_MAP = {"<": "&lt;", ">": "&gt;", "'": "&quot;", "&": "&amp;"}
