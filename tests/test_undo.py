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
    data = json.loads(journal.journal_path().read_text())
    assert data["version"] == 1
    assert data["renames"] == [
        {"src": str((tmp_path / "a1").resolve()), "dst": str((tmp_path / "b1").resolve())}
    ]


def test_preview_does_not_write_journal(tmp_path):
    make(tmp_path, a1="1")
    main(["^a", "b", str(tmp_path)])
    assert not journal.journal_path().exists()


def test_undo_previews_then_restores(tmp_path, capsys):
    make(tmp_path, a1="1", a2="2")
    main(["^a", "b", str(tmp_path), "--apply"])

    assert main(["undo"]) == 0
    assert "would be renamed" in capsys.readouterr().out
    assert contents(tmp_path) == {"b1": "1", "b2": "2"}

    assert main(["undo", "--apply"]) == 0
    assert "Restored 2 file(s)." in capsys.readouterr().out
    assert contents(tmp_path) == {"a1": "1", "a2": "2"}
    assert not journal.journal_path().exists()


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
    path = journal.journal_path()
    path.parent.mkdir(parents=True)
    path.write_text("{not json")
    assert main(["undo"]) == 2
    assert "cannot read undo journal" in capsys.readouterr().err
