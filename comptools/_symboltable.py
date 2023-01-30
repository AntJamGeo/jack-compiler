from comptools._error import JackError


class SymbolTable:
    def __init__(self):
        self._class_table = {}
        self._subroutine_table = {}
        self.var_count = {
            "static": 0,
            "this": 0,
            "argument": 0,
            "local": 0
        }

    def start_subroutine(self):
        self._subroutine_table = {}
        self.var_count["argument"] = 0
        self.var_count["local"] = 0

    def define(self, name, type_, kind):
        if kind in _CLASS_VAR:
            self._class_table[name] = {
                "kind": kind,
                "type": type_,
                "index": self.var_count[kind]
            }
        elif kind in _SUBROUTINE_VAR:
            self._subroutine_table[name] = {
                "kind": kind,
                "type": type_,
                "index": self.var_count[kind]
            }
        else:
            raise KeyError(f"Invalid variable kind: {kind}.")
        self.var_count[kind] += 1

    def get_var(self, name):
        variable = self._subroutine_table.get(name)
        return self._class_table.get(name) if variable is None else variable


_CLASS_VAR = frozenset(("static", "this"))
_SUBROUTINE_VAR = frozenset(("argument", "local"))
