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
