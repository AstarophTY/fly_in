from errors import FileError
from pathlib import Path


class Parsing:
    def __init__(self, map_file: str) -> None:
        self.map_file = Path(map_file)
        self.content = self._read_file(self.map_file)
        self._parse_map()

    def _split_content(self):
        return [s for s in self.content.split("\n")
                if not s.startswith("#") and len(s) > 1]

    def _parse_map(self):
        lines = self._split_content()
        print(lines)

    @staticmethod
    def _read_file(file: Path) -> str:
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
