
from parsing import Parsing
from errors import print_error, ArgumentsError
from sys import argv


def get_file() -> str:
    if len(argv) < 2:
        raise ArgumentsError("Not enough arguments", 1)

    if len(argv) > 2:
        raise ArgumentsError("Too many arguments", 2)

    return argv[1]


def main() -> None:
    try:
        parsing = Parsing(get_file())
    except Exception as e:
        print_error(f"{e}")


if __name__ == "__main__":
    main()
