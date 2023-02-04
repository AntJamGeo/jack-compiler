from _writers._base import Writer


class XMLWriter(Writer):
    def __init__(self):
        super().__init__()
        self._indent = ''

    def load_class(self, class_name):
        super().load_class(class_name, ".xml")

    def write(self, tag, token):
        self._file.write(
            f"{self._indent}<{tag}> "
            f"{_XML_MAP.get(token, token)} "
            f"</{tag}>\n"
        )

    def open_block(self, block):
        self._file.write(f"{self._indent}<{block}>\n")
        self._indent += ' ' * _INDENT_SPACES

    def close_block(self, block):
        self._indent = self._indent[:-_INDENT_SPACES]
        self._file.write(f"{self._indent}</{block}>\n")

_INDENT_SPACES = 2
_XML_MAP = {"<": "&lt;", ">": "&gt;", "'": "&quot;", "&": "&amp;"}
