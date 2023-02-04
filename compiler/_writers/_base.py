class Writer:
    def __init__(self):
        self._class_name = None
        self.file_name = None
        self._file = None

    def load_class(self, class_name, ext):
        self._class_name = class_name
        self.file_name = class_name + ext

    def __enter__(self):
        self._file = open(self.file_name, "w")
        return self

    def __exit__(self, *args):
        self._file.close()
