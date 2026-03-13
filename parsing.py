from errors import FileError, ParsingError
from pathlib import Path
from pydantic import ValidationError
from typing import Any
from validator import ParsingValidator
import re


class Parsing:
    """Parse the value of file
    """
    HUB_METADATA = {"zone", "color", "max_drones"}
    CONNECTION_METADATA = {"max_link_capacity"}

    def __init__(self, map_file: str) -> None:
        """Build parsing object

        Args:
            map_file (str): The path of the map file
        """
        self.map_file = Path(map_file)
        self.content = self._read_file(self.map_file)
        self.map_data = self._parse_map()
        return self._validate()

    def _split_content(self) -> list[str]:
        """Split the content of the file with \n and don't take #

        Returns:
            list[str]: Content split with /n and don't starts with #
        """
        return [s for s in self.content.split("\n")
                if not s.strip().startswith("#") and len(s) > 1]

    def _parse_hub(self, line: str) -> dict[str, Any] | None:
        search_prefix = (
            "hub:" if line.startswith("hub:") else
            ("start_hub:" if line.startswith("start_hub:") else
             ("end_hub:" if line.startswith("end_hub:") else None))
        )

        if search_prefix is None:
            return None

        meta_match = re.search(r"\[(.*?)\]$", line)
        metadata_raw = None

        if "[" in line:
            if not meta_match or line.count("[") > 1:
                raise ParsingError(
                    "Metadata must be unique and at the end of the line",
                    11
                )

            metadata_raw = meta_match.group(1)
            line = line[:meta_match.start()].strip()

        parts = line.removeprefix(search_prefix).split()
        if len(parts) < 3:
            raise ParsingError("Missing arguments for hub (name, x, y)", 13)

        dict_metadata = None
        if metadata_raw:
            dict_metadata = {}
            for item in metadata_raw.split():
                if "=" not in item or item.count("=") > 1:
                    raise ParsingError(
                        "Invalid metadata format (key=value)",
                        12
                    )

                key, val = item.split("=")
                if key not in self.HUB_METADATA:
                    allowed = ", ".join(sorted(self.HUB_METADATA))
                    raise ParsingError(
                        f"Invalid hub metadata key '{key}'. "
                        f"Allowed: {allowed}",
                        18
                    )
                dict_metadata[key] = int(val) if val.isnumeric() else val

        return {
            "name": parts[0],
            "coords": (int(parts[1]), int(parts[2])),
            "metadata": dict_metadata
        }

    def _parse_connection(self, line: str) -> dict[str, dict | str] | None:
        if not line.startswith("connection:"):
            return None

        meta_match = re.search(r"\[(.*?)\]$", line)
        metadata_raw = None

        if "[" in line:
            if not meta_match or line.count("[") > 1:
                raise ParsingError(
                    "Metadata must be unique and at the end of the line",
                    11
                )

            metadata_raw = meta_match.group(1)
            line = line[:meta_match.start()].strip()

        parts = line.removeprefix("connection:").strip().split("-")
        if len(parts) < 2:
            raise ParsingError(
                "Missing arguments for connection (<name1>-<name2>)",
                13
            )

        if len(parts) > 2:
            raise ParsingError(
                "Too many arguments for connection (<name1>-<name2>)",
                13
            )

        dict_metadata = None
        if metadata_raw:
            dict_metadata = {}
            for item in metadata_raw.split():
                if "=" not in item or item.count("=") > 1:
                    raise ParsingError(
                        "Invalid metadata format (key=value)",
                        12
                    )

                key, val = item.split("=")
                if key not in self.CONNECTION_METADATA:
                    allowed = ", ".join(
                        sorted(self.CONNECTION_METADATA)
                    )
                    raise ParsingError(
                        f"Invalid connection metadata key '{key}'. "
                        f"Allowed: {allowed}",
                        18
                    )
                dict_metadata[key] = int(val) if val.isnumeric() else val

        return {
            "zone_a": parts[0],
            "zone_b": parts[1],
            "metadata": dict_metadata
        }

    def _parse_map(self) -> dict[str, Any]:
        """Parse the values and check if the file is in good format

        Raises:
            ParsingError: Check if nb_drones is the first lines
        """
        lines = self._split_content()
        map_data: dict[str, Any] = {
            "hubs": [],
            "connections": []
        }

        # Parsing nb_drones
        if len(lines) > 0 and lines[0] and lines[0].startswith("nb_drones: "):
            nb_drones_str = lines[0].replace("nb_drones: ", "", 1)
            if not nb_drones_str.isnumeric():
                raise ParsingError("nb_drones must be numbers", 9)
            map_data.update({"nb_drones": int(nb_drones_str)})
        else:
            raise ParsingError("nb_drones must be the first line", 8)

        # Parsing all lines and raise error if is undefined
        for n, line in enumerate(lines[1:]):
            if line.startswith("hub:"):
                map_data["hubs"].append(self._parse_hub(line))
            elif line.startswith("start_hub:"):
                if map_data.get("start_hub") is not None:
                    raise ParsingError("You can only have one start_hub", 16)
                map_data.update({"start_hub": self._parse_hub(line)})
            elif line.startswith("end_hub:"):
                if map_data.get("end_hub") is not None:
                    raise ParsingError("You can only have one end_hub", 15)
                map_data.update({"end_hub": self._parse_hub(line)})
            elif line.startswith("connection:"):
                map_data["connections"].append(self._parse_connection(line))
            else:
                raise ParsingError(f"{line} is undefined in parsing", 14)

        return map_data

    def _validate(self) -> None:
        """Validate map_data with ParsingValidator and replace it with the
        validated model output.

        Raises:
            ParsingError: If the data fails Pydantic validation
        """
        try:
            validated = ParsingValidator(**self.map_data)
            self.map_data = validated.model_dump()
        except ValidationError as e:
            errors = e.errors()
            msg = errors[0]["msg"] if errors else "Validation failed"
            raise ParsingError(msg, 17)

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
