"""Carry out a planned batch of renames on disk."""

import os
import uuid
from pathlib import Path

from .planner import Rename


def apply(renames: list[Rename]) -> None:
    """Rename every file in two phases so swaps and cycles work.

    Each source is first moved to a unique temporary name in its own directory,
    then each temporary file is moved to its target. If any step fails, the
    steps already done are undone in reverse order and the error is re-raised.
    """
    batch = uuid.uuid4().hex[:8]
    done: list[tuple[Path, Path]] = []
    try:
        temps = []
        for i, r in enumerate(renames):
            temp = r.src.parent / f".rx-rename-{batch}-{i}"
            _move(r.src, temp, done)
            temps.append(temp)
        for temp, r in zip(temps, renames):
            _move(temp, r.dst, done)
    except OSError:
        for src, dst in reversed(done):
            os.rename(dst, src)
        raise


def _move(src: Path, dst: Path, done: list[tuple[Path, Path]]) -> None:
    # os.rename silently replaces files on POSIX, so refuse explicitly.
    if dst.exists() or dst.is_symlink():
        raise FileExistsError(f"{dst} already exists")
    os.rename(src, dst)
    done.append((src, dst))
