class JackError(Exception):
    def __init__(self, file_path, message):
        self.message = f"Error in {file_path}: {message}"
