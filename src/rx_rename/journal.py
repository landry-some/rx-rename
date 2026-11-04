"""Record each applied batch so it can be undone."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .planner import Rename

VERSION = 1


def history_dir() -> Path:
    state = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    return Path(state) / "rx-rename" / "history"


def batch_path(batch_id: int) -> Path:
    return history_dir() / f"{batch_id}.json"


def batch_ids() -> list[int]:
    """Return the ids of the batches that can still be undone, oldest first."""
    if not history_dir().is_dir():
        return []
    return sorted(int(p.stem) for p in history_dir().glob("*.json") if p.stem.isdigit())


def save(renames: list[Rename]) -> int:
    """Record a batch and return its id, one more than the newest id so far."""
    batch_id = max(batch_ids(), default=0) + 1
    path = batch_path(batch_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "version": VERSION,
        "applied_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "renames": [
            {"src": str(r.src.resolve()), "dst": str(r.dst.resolve())} for r in renames
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
    return batch_id


def load(batch_id: int) -> dict:
    """Return a recorded batch. Raises OSError or ValueError if it is unreadable."""
    path = batch_path(batch_id)
    data = json.loads(path.read_text())
    if data.get("version") != VERSION:
        raise ValueError(f"unsupported journal version in {path}")
    return data


def undo_renames(data: dict) -> list[Rename]:
    """Return the renames that would reverse a recorded batch."""
    return [Rename(Path(e["dst"]), Path(e["src"]).name) for e in data["renames"]]


def clear(batch_id: int) -> None:
    batch_path(batch_id).unlink(missing_ok=True)
