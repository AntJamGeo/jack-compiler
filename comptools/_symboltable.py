class SymbolTable:
    def __init__(self):
        self._class_table = {}
        self._subroutine_table = {}
        self._var_count = {
            "static": 0,
            "field": 0,
            "argument": 0,
            "var": 0
        }

    def start_subroutine(self):
        self._subroutine_table = {}
        self._var_count["argument"] = 0
        self._var_count["var"] = 0

    def define(self, name, type_, kind):
        if kind in _CLASS_VAR:
            self._class_table[name] = {
                "kind": kind,
                "type": type_,
                "index": self._var_count[kind]
            }
        elif kind in _SUBROUTINE_VAR:
            self._subroutine_table[name] = {
                "kind": kind,
                "type": type_,
                "index": self._var_count[kind]
            }
        else:
            raise KeyError(f"Invalid variable kind: {kind}.")
        self._var_count[kind] += 1

    def kind_of(self, name):
        return self._get_variable(name)["kind"]

    def type_of(self, name):
        return self._get_variable(name)["type"]

    def index_of(self, name):
        return self._get_variable(name)["index"]

    def _get_variable(self, name):
        variable = self._subroutine_table.get(name)
        if variable is None:
            variable = self._class_table.get(name)
        return variable


_CLASS_VAR = frozenset(("static", "field"))
_SUBROUTINE_VAR = frozenset(("argument", "var"))
