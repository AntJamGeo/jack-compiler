from comptools._writers._base import Writer


class VMWriter(Writer):
    def load_class(self, class_name):
        super().load_class(class_name, ".vm")

    def write(self, stuff):
        pass

    def push(self, segment, index):
        self._file.write(f"push {segment} {index}\n")

    def pop(self, segment, index):
        self._file.write(f"pop {segment} {index}\n")

    def arithmetic(self, command):
        self._file.write(f"{command}\n")

    def label(self, label):
        self._file.write(f"label {label}\n")

    def goto(self, label):
        self._file.write(f"goto {label}\n")

    def if_goto(self, label):
        self._file.write(f"if-goto {label}\n")

    def call(self, name, n_args):
        self._file.write(f"call {name} {n_args}\n")

    def function(self, name, n_vars):
        self._file.write(f"function {name} {n_vars}\n")

    def ret(self):
        self._file.write("return\n")
