
from parsing import Parsing
from errors import print_error, ArgumentsError
from sys import argv


def get_file() -> str:
    """Return path of file if input of the program is valid

    Raises:
        ArgumentsError: Check the size of arguments
                        if less or equal than 2
        ArgumentsError: Check the size of arguments
                        if is greater or equal than 2

    Returns:
        str: Return path of file
    """
    if len(argv) < 2:
        raise ArgumentsError("Not enough arguments", 1)

    if len(argv) > 2:
        raise ArgumentsError("Too many arguments", 2)

    return argv[1]


def main() -> None:
    """These are the first functions executed
    """
    try:
        parsing = Parsing(get_file())
    except Exception as e:
        print_error(f"{e}")


if __name__ == "__main__":
    main()
