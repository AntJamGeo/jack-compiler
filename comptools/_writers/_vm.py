from comptools._writers._base import Writer


class VMWriter(Writer):
    def load_class(self, class_name):
        super().load_class(class_name, ".vm")

    def write(self, stuff):
        self._file.write(stuff)

