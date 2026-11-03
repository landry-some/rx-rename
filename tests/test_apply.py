import os
import re
from pathlib import Path

import pytest

from rx_rename import executor
from rx_rename.cli import main
from rx_rename.planner import plan


def make(tmp_path: Path, **files: str) -> None:
    for name, content in files.items():
        (tmp_path / name).write_text(content)


def contents(tmp_path: Path) -> dict[str, str]:
    return {p.name: p.read_text() for p in tmp_path.iterdir()}


def test_apply_renames_files(tmp_path, capsys):
    make(tmp_path, **{"IMG_1.jpg": "one", "IMG_2.jpg": "two"})
    assert main([r"IMG_(\d)", r"photo-\1", str(tmp_path), "--apply"]) == 0
    assert contents(tmp_path) == {"photo-1.jpg": "one", "photo-2.jpg": "two"}
    assert "Renamed 2 file(s)." in capsys.readouterr().out


def test_apply_swap(tmp_path):
    make(tmp_path, a="A", b="B")
    renames = plan([tmp_path / "a", tmp_path / "b"], re.compile("^(a|b)$"),
                   lambda m: {"a": "b", "b": "a"}[m.group(1)])
    executor.apply(renames)
    assert contents(tmp_path) == {"a": "B", "b": "A"}


def test_apply_three_way_cycle(tmp_path):
    make(tmp_path, a="A", b="B", c="C")
    nxt = {"a": "b", "b": "c", "c": "a"}
    renames = plan(sorted(tmp_path.iterdir()), re.compile("^.$"),
                   lambda m: nxt[m.group(0)])
    executor.apply(renames)
    assert contents(tmp_path) == {"b": "A", "c": "B", "a": "C"}


def test_apply_refuses_with_conflicts(tmp_path):
    make(tmp_path, **{"old.txt": "old", "new.txt": "new"})
    assert main(["^old", "new", str(tmp_path), "--apply"]) == 1
    assert contents(tmp_path) == {"old.txt": "old", "new.txt": "new"}


def test_failure_rolls_back(tmp_path, monkeypatch, capsys):
    make(tmp_path, a1="1", a2="2", a3="3")
    real_rename = os.rename
    calls = []

    def flaky(src, dst):
        calls.append(src)
        if len(calls) == 5:  # fail during the second phase
            raise PermissionError("simulated")
        real_rename(src, dst)

    monkeypatch.setattr(executor.os, "rename", flaky)
    assert main(["^a", "b", str(tmp_path), "--apply"]) == 1
    assert contents(tmp_path) == {"a1": "1", "a2": "2", "a3": "3"}
    assert "rolled back" in capsys.readouterr().err


def test_move_never_overwrites(tmp_path):
    make(tmp_path, a="A", b="B")
    with pytest.raises(FileExistsError):
        executor._move(tmp_path / "a", tmp_path / "b", [])
    assert contents(tmp_path) == {"a": "A", "b": "B"}
