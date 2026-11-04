import os
import re
from datetime import datetime
from pathlib import Path

import pytest

from rx_rename.cli import main
from rx_rename.planner import plan


def setup(tmp_path: Path, *names: str) -> list[Path]:
    for name in names:
        (tmp_path / name).write_text("")
    return [tmp_path / n for n in names]


def new_names(paths: list[Path], pattern: str, replacement: str) -> list[str]:
    return [r.new_name for r in plan(paths, re.compile(pattern), replacement)]


def test_counter_numbers_renames_in_order(tmp_path):
    paths = setup(tmp_path, "b.jpg", "a.jpg", "c.jpg")
    assert new_names(paths, r"^\w+", "photo-{n}") == [
        "photo-1.jpg",
        "photo-2.jpg",
        "photo-3.jpg",
    ]


def test_counter_format_spec(tmp_path):
    paths = setup(tmp_path, "x.txt")
    assert new_names(paths, r"^x", "{n:03}") == ["001.txt"]


def test_counter_skips_files_that_do_not_change(tmp_path):
    paths = setup(tmp_path, "a.txt", "keep.md", "b.txt")
    assert new_names(paths, r"^(\w+)\.txt$", r"{n}-\1.txt") == ["1-a.txt", "2-b.txt"]


def test_counter_next_to_group_reference_is_not_a_bigger_group(tmp_path):
    paths = setup(tmp_path, "a")
    assert new_names(paths, "^(a)$", r"\1{n}") == ["a1"]


def test_mtime_token(tmp_path):
    [path] = setup(tmp_path, "scan.pdf")
    stamp = datetime(2024, 3, 9, 14, 30).timestamp()
    os.utime(path, (stamp, stamp))
    assert new_names([path], "^scan", "{mtime}") == ["2024-03-09.pdf"]
    assert new_names([path], "^scan", "{mtime:%Y%m%d-%H%M}") == ["20240309-1430.pdf"]


def test_tokens_combine_with_case_escapes(tmp_path):
    [path] = setup(tmp_path, "note.txt")
    stamp = datetime(2024, 3, 9).timestamp()
    os.utime(path, (stamp, stamp))
    assert new_names([path], r"^note", r"\U{mtime:%b}\E-{n}") == ["MAR-1.txt"]


def test_other_braces_are_literal(tmp_path):
    paths = setup(tmp_path, "a")
    assert new_names(paths, "^a$", "{x}{n:02}") == ["{x}01"]


def test_bad_token_format_is_an_error(tmp_path):
    paths = setup(tmp_path, "a")
    with pytest.raises(re.error, match="bad token"):
        new_names(paths, "a", "{n:q}")


def test_cli_numbers_files(tmp_path, capsys):
    setup(tmp_path, "IMG_9.jpg", "IMG_10.jpg")
    assert main([r"^IMG_\d+", "holiday-{n:02}", str(tmp_path), "--apply"]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "holiday-01.jpg",
        "holiday-02.jpg",
    ]


def test_cli_bad_token_exits_2(tmp_path, capsys):
    setup(tmp_path, "a")
    assert main(["a", "{n:q}", str(tmp_path)]) == 2
    assert "bad token" in capsys.readouterr().err
