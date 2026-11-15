"""Solve every map in ``maps/`` without the 3D view and print the turn count.

Usage: uv run python benchmark.py
"""
from pathlib import Path
from sys import exit

from parsing import Parsing
from pathfinding import PathFinding


def main() -> None:
    """Run the pathfinding on all maps and print a Markdown table."""
    root = Path(__file__).resolve().parent / "maps"
    failed = False

    print("| Map | Drones | Turns |")
    print("| --- | ---: | ---: |")
    for map_file in sorted(root.rglob("*.txt")):
        name = map_file.relative_to(root).as_posix()
        try:
            parsing = Parsing(str(map_file))
            result = PathFinding(parsing.map_data)
        except Exception as e:
            print(f"| `{name}` | - | error: {e} |")
            failed = True
            continue
        drones = parsing.map_data.get("nb_drones", "?")
        print(f"| `{name}` | {drones} | {len(result.output)} |")

    if failed:
        exit(1)


if __name__ == "__main__":
    main()
