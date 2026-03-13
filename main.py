
from parsing import Parsing
from errors import print_error, ArgumentsError
from pathfinding import PathFinding
from sys import argv
from graphics import Graphics
from pathlib import Path
import questionary


def _get_available_maps() -> list[str]:
    """Return all available map files in the maps directory.

    Returns:
        list[str]: Relative map paths sorted alphabetically
    """
    root = Path(__file__).resolve().parent
    maps_root = root / "maps"
    if not maps_root.exists():
        return []

    map_files = sorted(maps_root.rglob("*.txt"))
    return [str(path.relative_to(root)).replace("\\", "/")
            for path in map_files]


def _pick_map_interactive(available_maps: list[str]) -> str | None:
    """Pick a map interactively with arrows and search.

    Args:
        available_maps (list[str]): Candidate map files

    Returns:
        str | None: Selected map path or None if cancelled
    """
    selected_map = questionary.autocomplete(
        "Select a map:",
        choices=available_maps,
        match_middle=True,
        validate=lambda text: (
            True if text in available_maps else "Please select an existing map"
        ),
    ).ask()
    return selected_map if isinstance(selected_map, str) else None


def _get_file() -> str:
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
        available_maps = _get_available_maps()

        if available_maps:
            selected_map = _pick_map_interactive(available_maps)
            if selected_map is not None:
                print(f"Selected map: {selected_map}")
                return selected_map

        print("No map provided.")
        print("Usage: uv run python main.py <map_file>")
        if available_maps:
            print("\nAvailable maps:")
            for map_file in available_maps:
                print(f"- {map_file}")
        raise ArgumentsError("Not enough arguments", 1)

    if len(argv) > 2:
        raise ArgumentsError("Too many arguments", 2)

    return argv[1]


def main() -> None:
    """These are the first functions executed
    """
    try:
        parsing = Parsing(_get_file())
    except Exception as e:
        print_error(f"{e}")
        return

    data = PathFinding(parsing.map_data)
    print("\n".join(data.output))

    Graphics(data)


if __name__ == "__main__":
    main()
