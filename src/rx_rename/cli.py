"""Command-line entry point."""

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

from . import __version__
from .executor import apply
from .planner import Conflict, Rename, find_conflicts, plan


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
    parser.add_argument(
        "--apply", action="store_true", help="actually rename the files"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="descend into subdirectories"
    )
    parser.add_argument(
        "--glob", metavar="GLOB", help="only consider names matching GLOB, e.g. '*.jpg'"
    )
    parser.add_argument(
        "--dirs", action="store_true", help="rename directories as well as files"
    )
    parser.add_argument(
        "-i", "--ignore-case", action="store_true", help="match the pattern case-insensitively"
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def collect(
    paths: list[Path],
    recursive: bool = False,
    glob: str | None = None,
    dirs: bool = False,
) -> list[Path]:
    """Expand directory arguments into the entries to consider for renaming.

    Files named directly are always kept. Entries found inside a directory are
    kept if they are files (or directories, with dirs=True) matching glob.
    """
    found = []
    for path in paths:
        if not path.exists() and not path.is_symlink():
            raise FileNotFoundError(path)
        if not path.is_dir():
            found.append(path)
            continue
        for parent, subdirs, files in os.walk(path):
            subdirs.sort()
            names = sorted(files + subdirs) if dirs else sorted(files)
            for name in names:
                if glob is None or fnmatch.fnmatch(name, glob):
                    found.append(Path(parent) / name)
            if not recursive:
                break
    return found


def print_preview(
    renames: list[Rename], conflicts: list[Conflict], applying: bool = False
) -> None:
    problems = {c.rename: c.reason for c in conflicts}
    width = max(len(str(r.src)) for r in renames)
    for r in renames:
        line = f"{str(r.src):<{width}}  ->  {r.dst}"
        if r in problems:
            line = f"{line}  !! {problems[r]}"
        print(line)
    if conflicts:
        print(f"\n{len(conflicts)} conflict(s) must be fixed before applying.")
        print("Nothing was changed.")
    elif not applying:
        print(f"\n{len(renames)} file(s) would be renamed. Nothing was changed.")
        print("Run again with --apply to rename them.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        regex = re.compile(args.pattern, re.IGNORECASE if args.ignore_case else 0)
        paths = collect(args.paths, args.recursive, args.glob, args.dirs)
        renames = plan(paths, regex, args.replacement)
    except re.error as exc:
        print(f"rx-rename: bad pattern or replacement: {exc}", file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(f"rx-rename: no such file or directory: {exc}", file=sys.stderr)
        return 2

    if not renames:
        print("No files would be renamed.")
        return 0
    conflicts = find_conflicts(renames)
    print_preview(renames, conflicts, args.apply)
    if conflicts:
        return 1
    if args.apply:
        try:
            apply(renames)
        except OSError as exc:
            print(f"rx-rename: rename failed, changes rolled back: {exc}", file=sys.stderr)
            return 1
        print(f"\nRenamed {len(renames)} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
