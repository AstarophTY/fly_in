from sys import stderr


class Color:
    """Class with patterns of colors
    """
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'


def print_error(error: str) -> None:
    """Print error on stderr with format

    Args:
        error (str): Error description
    """
    print(
        f"[{Color.RED + Color.BOLD}ERROR{Color.END}] {error}",
        file=stderr
    )


class ArgumentsError(Exception):
    """Create error for arguments error
    """
    def __init__(self, message: str, error_code: int):
        """Build default message for arguments error

        Args:
            message (str): Error description
            error_code (int): Error id
        """
        error = f"Arguments error: {message} (Code: {error_code})\n"
        output = f"[{Color.BLUE + Color.BOLD}Format{Color.END}]: \
uv run python main.py 01_linear_path.txt"
        super().__init__(error + output)


class FileError(Exception):
    """Create error for file error
    """
    def __init__(self, message: str, error_code: int):
        """Build default message for file error

        Args:
            message (str): Error description
            error_code (int): Error id
        """
        error = f"File error: {message} (Code: {error_code})"
        super().__init__(error)


class ParsingError(Exception):
    """Create error for parsing error
    """
    def __init__(self, message: str, error_code: int):
        """Build default message for parsing error

        Args:
            message (str): Error description
            error_code (int): Error id
        """
        error = f"Parsing error: {message} (Code: {error_code})"
        super().__init__(error)
