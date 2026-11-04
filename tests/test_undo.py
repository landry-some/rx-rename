import json
from pathlib import Path

from rx_rename import journal
from rx_rename.cli import main


def make(root: Path, **files: str) -> None:
    for name, content in files.items():
        (root / name).write_text(content)


def contents(root: Path) -> dict[str, str]:
    return {p.name: p.read_text() for p in root.iterdir()}


def test_apply_writes_journal(tmp_path):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path), "--apply"])
    assert journal.batch_ids() == [1]
    data = json.loads(journal.batch_path(1).read_text())
    assert data["version"] == 1
    assert data["renames"] == [
        {"src": str((tmp_path / "a1").resolve()), "dst": str((tmp_path / "b1").resolve())}
    ]


def test_preview_does_not_write_journal(tmp_path):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path)])
    assert journal.batch_ids() == []


def test_undo_previews_then_restores(tmp_path, capsys):
    make(tmp_path, a1="1", a2="2")
    main(["^a", "b", str(tmp_path), "--apply"])

    assert main(["undo"]) == 0
    assert "would be renamed" in capsys.readouterr().out
    assert contents(tmp_path) == {"b1": "1", "b2": "2"}

    assert main(["undo", "--apply"]) == 0
    assert "Restored 2 file(s) from batch 1." in capsys.readouterr().out
    assert contents(tmp_path) == {"a1": "1", "a2": "2"}
    assert journal.batch_ids() == []


def test_undo_swap(tmp_path):
    make(tmp_path, a="A", b="B")
    main(["^(a|b)$", "\\1-tmp", str(tmp_path), "--apply"])
    main(["undo", "--apply"])
    assert contents(tmp_path) == {"a": "A", "b": "B"}


def test_nothing_to_undo(capsys):
    assert main(["undo"]) == 0
    assert "Nothing to undo." in capsys.readouterr().out


def test_undo_refuses_if_file_was_moved(tmp_path, capsys):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path), "--apply"])
    (tmp_path / "b1").rename(tmp_path / "elsewhere")
    assert main(["undo", "--apply"]) == 1
    assert "moved or deleted since" in capsys.readouterr().out
    assert contents(tmp_path) == {"elsewhere": "1"}


def test_undo_refuses_if_original_name_was_reused(tmp_path, capsys):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path), "--apply"])
    make(tmp_path, a1="new file")
    assert main(["undo", "--apply"]) == 1
    assert "target already exists" in capsys.readouterr().out
    assert contents(tmp_path) == {"a1": "new file", "b1": "1"}


def test_corrupt_journal_exits_2(capsys):
    path = journal.batch_path(1)
    path.parent.mkdir(parents=True)
    path.write_text("{not json")
    assert main(["undo"]) == 2
    assert "cannot read undo journal" in capsys.readouterr().err


def test_each_apply_adds_a_batch_and_undo_reverses_the_newest(tmp_path):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path), "--apply"])
    main(["^b", "c", str(tmp_path), "--apply"])
    assert journal.batch_ids() == [1, 2]

    assert main(["undo", "--apply"]) == 0
    assert contents(tmp_path) == {"b1": "1"}
    assert main(["undo", "--apply"]) == 0
    assert contents(tmp_path) == {"a1": "1"}
    assert journal.batch_ids() == []


def test_undo_older_batch_by_id(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "y").mkdir()
    make(tmp_path / "x", a1="1")
    make(tmp_path / "y", a2="2")
    main(["^a", "b", str(tmp_path / "x"), "--apply"])
    main(["^a", "b", str(tmp_path / "y"), "--apply"])

    assert main(["undo", "1", "--apply"]) == 0
    assert contents(tmp_path / "x") == {"a1": "1"}
    assert contents(tmp_path / "y") == {"b2": "2"}
    assert journal.batch_ids() == [2]


def test_new_batch_gets_id_after_the_newest(tmp_path):
    make(tmp_path, a1="1", x="x")
    main(["^a", "b", str(tmp_path), "--apply"])
    main(["^x$", "y", str(tmp_path), "--apply"])
    main(["undo", "1", "--apply"])
    main(["^a", "c", str(tmp_path), "--apply"])
    assert journal.batch_ids() == [2, 3]


def test_undo_unknown_id_exits_2(tmp_path, capsys):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path), "--apply"])
    assert main(["undo", "7"]) == 2
    assert "no batch 7" in capsys.readouterr().err


def test_undo_list(tmp_path, capsys):
    make(tmp_path, a1="1", a2="2")
    main(["^a1", "b1", str(tmp_path), "--apply"])
    main(["^a2", "b2", str(tmp_path), "--apply"])
    capsys.readouterr()

    assert main(["undo", "--list"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert lines[0].split()[0] == "2" and lines[0].endswith("->  b2")
    assert lines[1].split()[0] == "1" and lines[1].endswith("->  b1")


def test_undo_list_when_empty(capsys):
    assert main(["undo", "--list"]) == 0
    assert "Nothing to undo." in capsys.readouterr().out
