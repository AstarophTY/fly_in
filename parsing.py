from errors import FileError, ParsingError
from pathlib import Path


class Parsing:
    """Parse the value of file
    """
    def __init__(self, map_file: str) -> None:
        """Build parsing object

        Args:
            map_file (str): The path of the map file
        """
        self.map_file = Path(map_file)
        self.content = self._read_file(self.map_file)
        self._parse_map()

    def _split_content(self) -> list[str]:
        """Split the content of the file with \n and don't take #

        Returns:
            list[str]: Content split with /n and don't starts with #
        """
        return [s for s in self.content.split("\n")
                if not s.strip().startswith("#") and len(s) > 1]

    def _parse_hub(self) -> dict:
        return

    def _parse_map(self) -> dict[str, str | dict]:
        """Parse the values and check if the file is in good format

        Raises:
            ParsingError: Check if nb_drones is the first lines
        """
        lines = self._split_content()
        map_data = {}

        # Parsing nb_drones
        if len(lines) > 0 and lines[0] and lines[0].startswith("nb_drones: "):
            nb_drones_str = lines[0].replace("nb_drones: ", "", 1)
            if not nb_drones_str.isnumeric():
                raise Parsing("nb_drones must be numbers", 9)
            map_data.update({"nb_drones": nb_drones_str})
        else:
            raise ParsingError("nb_drones must be the first line", 8)
        # for n, line in enumerate(1, lines):
        print(map_data)
        return map_data

    @staticmethod
    def _read_file(file: Path) -> str:
        """Open file and check error

        Args:
            file (Path): File path will be read

        Raises:
            FileError: FileNotFound
            FileError: PermissionError
            FileError: IsADirectoryError
            FileError: NotADirectoryError
            FileError: Exception

        Returns:
            str: The content of the file
        """
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
