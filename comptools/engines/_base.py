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
