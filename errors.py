from sys import stderr


class Color:
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
    print(
        f"[{Color.RED + Color.BOLD}ERROR{Color.END}] {error}",
        file=stderr
    )


class ArgumentsError(Exception):
    def __init__(self, message: str, error_code: int):
        error = f"Arguments error: {message} (Code: {error_code})\n"
        output = f"[{Color.BLUE + Color.BOLD}Format{Color.END}]: \
uv run python main.py 01_linear_path.txt"
        super().__init__(error + output)


class FileError(Exception):
    def __init__(self, message: str, error_code: int):
        error = f"File error: {message} (Code: {error_code})"
        super().__init__(error)
