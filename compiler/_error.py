class JackError(Exception):
    def __init__(
            self,
            class_,
            line_no,
            line,
            error_index,
            type_="Syntax",
            info="invalid syntax"):
        error_loc = " " * error_index + "^"
        self.message = (
                "Error found:\n"
                f"  Class '{class_}', line {line_no}\n"
                f"    {line}\n"
                f"    {error_loc}\n"
                f"{type_}Error: {info}\n")
