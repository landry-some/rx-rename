import re
from pathlib import Path

from rx_rename.cli import main
from rx_rename.planner import plan


def touch(directory: Path, *names: str) -> None:
    for name in names:
        (directory / name).write_text("")


def test_plan_uses_groups_and_skips_unchanged(tmp_path):
    touch(tmp_path, "IMG_001.jpg", "notes.txt")
    paths = sorted(tmp_path.iterdir())
    renames = plan(paths, re.compile(r"IMG_(\d+)"), r"photo-\1")
    assert [(r.src.name, r.new_name) for r in renames] == [("IMG_001.jpg", "photo-001.jpg")]
    assert renames[0].dst == tmp_path / "photo-001.jpg"


def test_plan_only_touches_basename(tmp_path):
    sub = tmp_path / "a_dir"
    sub.mkdir()
    touch(sub, "a_file")
    renames = plan([sub / "a_file"], re.compile("a_"), "b_")
    assert renames[0].dst == sub / "b_file"


def test_preview_changes_nothing(tmp_path, capsys):
    touch(tmp_path, "draft 1.txt", "draft 2.txt")
    assert main([r"draft (\d)", r"final-\1", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "final-1.txt" in out and "final-2.txt" in out
    assert "2 file(s) would be renamed" in out
    assert sorted(p.name for p in tmp_path.iterdir()) == ["draft 1.txt", "draft 2.txt"]


def test_no_matches(tmp_path, capsys):
    touch(tmp_path, "a.txt")
    assert main(["zzz", "y", str(tmp_path)]) == 0
    assert "No files would be renamed." in capsys.readouterr().out


def test_bad_regex_exits_2(tmp_path, capsys):
    assert main(["(", "x", str(tmp_path)]) == 2
    assert "bad pattern" in capsys.readouterr().err


def test_bad_group_reference_exits_2(tmp_path, capsys):
    touch(tmp_path, "a.txt")
    assert main(["a", r"\2", str(tmp_path)]) == 2


def test_missing_path_exits_2(tmp_path, capsys):
    assert main(["a", "b", str(tmp_path / "nope")]) == 2
