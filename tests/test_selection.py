from pathlib import Path

from rx_rename.cli import collect, main


def tree(root: Path) -> None:
    (root / "sub").mkdir()
    (root / "sub" / "deep").mkdir()
    for rel in ["a.jpg", "b.txt", "sub/c.jpg", "sub/deep/d.jpg"]:
        (root / rel).write_text("")


def names(root: Path, paths: list[Path]) -> list[str]:
    return [p.relative_to(root).as_posix() for p in paths]


def test_default_is_files_in_top_directory(tmp_path):
    tree(tmp_path)
    assert names(tmp_path, collect([tmp_path])) == ["a.jpg", "b.txt"]


def test_recursive(tmp_path):
    tree(tmp_path)
    assert names(tmp_path, collect([tmp_path], recursive=True)) == [
        "a.jpg", "b.txt", "sub/c.jpg", "sub/deep/d.jpg"]


def test_glob(tmp_path):
    tree(tmp_path)
    assert names(tmp_path, collect([tmp_path], recursive=True, glob="*.jpg")) == [
        "a.jpg", "sub/c.jpg", "sub/deep/d.jpg"]


def test_dirs(tmp_path):
    tree(tmp_path)
    assert names(tmp_path, collect([tmp_path], dirs=True)) == ["a.jpg", "b.txt", "sub"]


def test_explicit_file_is_kept_regardless_of_glob(tmp_path):
    tree(tmp_path)
    assert collect([tmp_path / "b.txt"], glob="*.jpg") == [tmp_path / "b.txt"]


def test_ignore_case(tmp_path, capsys):
    (tmp_path / "Photo.JPG").write_text("")
    assert main(["jpg$", "jpeg", str(tmp_path)]) == 0
    assert "No files would be renamed." in capsys.readouterr().out
    assert main(["-i", "jpg$", "jpeg", str(tmp_path), "--apply"]) == 0
    assert (tmp_path / "Photo.jpeg").exists()


def test_dir_and_its_contents_in_one_batch_is_a_conflict(tmp_path, capsys):
    tree(tmp_path)
    assert main(["^(sub|c)", r"\1-x", str(tmp_path), "-r", "--dirs", "--apply"]) == 1
    assert "inside a directory that is also being renamed" in capsys.readouterr().out
    assert (tmp_path / "sub" / "c.jpg").exists()


def test_recursive_apply(tmp_path):
    tree(tmp_path)
    assert main([r"\.jpg$", ".jpeg", str(tmp_path), "-r", "--apply"]) == 0
    assert (tmp_path / "sub" / "deep" / "d.jpeg").exists()
    assert (tmp_path / "b.txt").exists()
