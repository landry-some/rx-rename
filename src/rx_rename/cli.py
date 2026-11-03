"""Command-line entry point."""

import argparse
import re
import sys
from pathlib import Path

from . import __version__
from .planner import Rename, plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rx-rename",
        description="Rename files with a regular expression. "
        "Shows what would change; nothing is renamed by default.",
    )
    parser.add_argument("pattern", help="regex matched against each file's basename")
    parser.add_argument(
        "replacement", help=r"replacement text; \1 or \g<name> refer to groups"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path(".")],
        help="files or directories to rename in (default: current directory)",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def collect(paths: list[Path]) -> list[Path]:
    """Expand directories into the files directly inside them."""
    found = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(p for p in path.iterdir() if p.is_file()))
        elif path.exists():
            found.append(path)
        else:
            raise FileNotFoundError(path)
    return found


def print_preview(renames: list[Rename]) -> None:
    width = max(len(str(r.src)) for r in renames)
    for r in renames:
        print(f"{str(r.src):<{width}}  ->  {r.dst}")
    print(f"\n{len(renames)} file(s) would be renamed. Nothing was changed.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        regex = re.compile(args.pattern)
        renames = plan(collect(args.paths), regex, args.replacement)
    except re.error as exc:
        print(f"rx-rename: bad pattern or replacement: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"rx-rename: no such file or directory: {exc}", file=sys.stderr)
        return 2

    if not renames:
        print("No files would be renamed.")
        return 0
    print_preview(renames)
    return 0


if __name__ == "__main__":
    sys.exit(main())
