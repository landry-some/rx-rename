"""Work out what each file would be renamed to, without changing anything on disk."""

import re
from dataclasses import dataclass
from datetime import datetime
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

    The replacement may use \\U, \\L or \\T to upper-, lower- or title-case
    what follows, up to \\E or the next case escape. {n} or {n:03} is the
    rename's position in the batch, counting from 1; {mtime} or
    {mtime:%Y%m%d} is the file's modification date.
    Raises re.error if the replacement refers to a group the pattern lacks
    or has a bad token format.
    """
    renames = []
    for path in paths:
        if not regex.search(path.name):
            continue
        substitute = replacement
        if isinstance(replacement, str):
            substitute = _substituter(replacement, path, len(renames) + 1)
        new_name = regex.sub(substitute, path.name)
        if new_name != path.name:
            renames.append(Rename(path, new_name))
    return renames


_SPECIAL = re.compile(r"\\\\|\\([ULTE])|\{(n|mtime)(?::([^}]*))?\}")
_CASES = {"U": str.upper, "L": str.lower, "T": str.title, "E": None}


def _substituter(replacement: str, path: Path, n: int):
    """Return the re.sub replacement function for path, the n-th file renamed.

    The replacement is split into templates that re expands, tokens filled in
    as plain text, and case escapes that apply to every piece after them.
    """
    parts = []  # (case function or None, text, whether text is a template)
    case = None
    start = 0
    for m in _SPECIAL.finditer(replacement):
        if m.group(0) == "\\\\":  # an escaped backslash, left for re to expand
            continue
        parts.append((case, replacement[start : m.start()], True))
        start = m.end()
        if m.group(1):
            case = _CASES[m.group(1)]
        else:
            parts.append((case, _token(m, path, n), False))
    parts.append((case, replacement[start:], True))

    def expand(match: re.Match) -> str:
        out = []
        for change_case, text, is_template in parts:
            if is_template:
                text = match.expand(text)
            out.append(change_case(text) if change_case else text)
        return "".join(out)

    return expand


def _token(m: re.Match, path: Path, n: int) -> str:
    name, spec = m.group(2), m.group(3)
    try:
        if name == "n":
            return format(n, spec or "")
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        return mtime.strftime(spec or "%Y-%m-%d")
    except ValueError as exc:
        raise re.error(f"bad token {m.group(0)}: {exc}") from None


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
