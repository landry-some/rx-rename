"""Record the last applied batch so it can be undone."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .planner import Rename

VERSION = 1


def journal_path() -> Path:
    state = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(state) / "rx-rename" / "last.json"


def save(renames: list[Rename]) -> Path:
    path = journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": VERSION,
        "applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "renames": [
            {"src": str(r.src.resolve()), "dst": str(r.dst.resolve())} for r in renames
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
    return path


def load_undo() -> list[Rename] | None:
    """Return the renames that would reverse the last batch, or None if there is none."""
    path = journal_path()
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    if data.get("version") != VERSION:
        raise ValueError(f"unsupported journal version in {path}")
    return [Rename(Path(e["dst"]), Path(e["src"]).name) for e in data["renames"]]


def clear() -> None:
    journal_path().unlink(missing_ok=True)
