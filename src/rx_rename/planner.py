"""Work out what each file would be renamed to, without touching the disk."""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rename:
    src: Path
    new_name: str

    @property
    def dst(self) -> Path:
        return self.src.parent / self.new_name


def plan(paths: list[Path], regex: re.Pattern, replacement: str) -> list[Rename]:
    """Return a Rename for every path whose basename the regex would change.

    Raises re.error if the replacement refers to a group the pattern lacks.
    """
    renames = []
    for path in paths:
        new_name = regex.sub(replacement, path.name)
        if new_name != path.name:
            renames.append(Rename(path, new_name))
    return renames


@dataclass(frozen=True)
class Conflict:
    rename: Rename
    reason: str


def find_conflicts(renames: list[Rename]) -> list[Conflict]:
    """Return every rename that cannot be applied safely, with the reason."""
    conflicts = []
    sources = {r.src.resolve() for r in renames}
    by_target: dict[Path, list[Rename]] = {}
    for r in renames:
        by_target.setdefault(r.dst.resolve(), []).append(r)

    for r in renames:
        reason = _name_problem(r.new_name)
        if reason is None and any(parent in sources for parent in r.src.resolve().parents):
            reason = "inside a directory that is also being renamed"
        if reason is None:
            target = r.dst.resolve()
            others = [o.src for o in by_target[target] if o is not r]
            if others:
                reason = "same new name as " + ", ".join(str(o) for o in others)
            elif r.dst.exists() and target not in sources:
                reason = "target already exists"
        if reason:
            conflicts.append(Conflict(r, reason))
    return conflicts


def _name_problem(name: str) -> str | None:
    if name == "":
        return "new name is empty"
    if name in (".", ".."):
        return f"new name is {name!r}"
    if "/" in name or "\0" in name:
        return "new name contains '/' or a NUL byte"
    return None
