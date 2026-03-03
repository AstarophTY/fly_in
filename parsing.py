from errors import ArgumentsError, FileError


class Parsing:
    def __init__(self, map_file: str) -> None:
        self.map_file = map_file
        self.content = self._read_file

    @staticmethod
    def _read_file(file: str) -> str:
        try:
            with open(file, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise FileError(f"No such file or directory: '{file}'", 3)
        except PermissionError:
            raise FileError(f"Permission denied: '{file}'", 4)
        except IsADirectoryError:
            raise FileError(f"Is a directory: {file}", 5)
        except NotADirectoryError:
            raise FileError(f"Not a directory: '{file}'", 6)
        except Exception as e:
            raise FileError(f"{e}", 7)
