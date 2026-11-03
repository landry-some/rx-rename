import re
from pathlib import Path

from rx_rename.cli import main
from rx_rename.planner import find_conflicts, plan


def setup(tmp_path: Path, *names: str) -> list[Path]:
    for name in names:
        (tmp_path / name).write_text("")
    return [tmp_path / n for n in names]


def reasons(tmp_path, names, pattern, replacement):
    renames = plan(setup(tmp_path, *names), re.compile(pattern), replacement)
    return {c.rename.src.name: c.reason for c in find_conflicts(renames)}


def test_no_conflicts(tmp_path):
    assert reasons(tmp_path, ["a1", "a2"], "a", "b") == {}


def test_two_files_same_target(tmp_path):
    found = reasons(tmp_path, ["x-1.txt", "y-1.txt"], r"^.-", "")
    assert set(found) == {"x-1.txt", "y-1.txt"}
    assert "same new name" in found["x-1.txt"]


def test_existing_target(tmp_path):
    found = reasons(tmp_path, ["old.txt", "new.txt"], "^old", "new")
    assert found == {"old.txt": "target already exists"}


def test_target_freed_by_another_rename_is_ok(tmp_path):
    # a -> b while b -> c: b will have moved away, so no conflict.
    renames = plan(setup(tmp_path, "a", "b"), re.compile("^(a|b)$"),
                   lambda m: {"a": "b", "b": "c"}[m.group(1)])
    assert find_conflicts(renames) == []


def test_swap_is_ok(tmp_path):
    renames = plan(setup(tmp_path, "a", "b"), re.compile("^(a|b)$"),
                   lambda m: {"a": "b", "b": "a"}[m.group(1)])
    assert find_conflicts(renames) == []


def test_bad_new_names(tmp_path):
    assert reasons(tmp_path, ["abc"], ".*", "") == {"abc": "new name is empty"}
    assert "'/'" in reasons(tmp_path, ["def"], "e", "/")["def"]
    assert reasons(tmp_path, ["ghi"], "^ghi$", "..") == {"ghi": "new name is '..'"}


def test_cli_marks_conflicts_and_exits_1(tmp_path, capsys):
    setup(tmp_path, "old.txt", "new.txt")
    assert main(["^old", "new", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "!! target already exists" in out
    assert "1 conflict(s)" in out
