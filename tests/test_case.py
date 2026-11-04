import re
from pathlib import Path

import pytest

from rx_rename.cli import main
from rx_rename.planner import plan


def new_names(names: list[str], pattern: str, replacement: str) -> list[str]:
    paths = [Path(n) for n in names]
    return [r.new_name for r in plan(paths, re.compile(pattern), replacement)]


@pytest.mark.parametrize(
    "pattern, replacement, expected",
    [
        (r"^(\w+)", r"\U\1", "MY_PHOTO.jpg"),
        (r"\.jpg$", r"\U.jpg", "my_photo.JPG"),
        (r"^([a-z]+)_([a-z]+)", r"\U\1\E_\2", "MY_photo.jpg"),
        (r"^(.*)\.jpg$", r"\T\1\E.jpg", "My_Photo.jpg"),
        (r"^my_([a-z]+)", r"\Lnew_\U\1", "new_PHOTO.jpg"),
    ],
)
def test_case_escapes(pattern, replacement, expected):
    assert new_names(["my_photo.jpg"], pattern, replacement) == [expected]


def test_lower_applies_to_literal_and_group_text():
    assert new_names(["IMG_0001.JPG"], r"^IMG_(\d+)\.JPG$", r"\LPhoto-\1.JPG") == [
        "photo-0001.jpg"
    ]


def test_escaped_backslash_is_not_a_case_escape():
    assert new_names(["a"], "a", r"\\U") == [r"\U"]


def test_bad_group_inside_case_escape_is_an_error():
    with pytest.raises(re.error):
        new_names(["a"], "a", r"\U\2")


def test_cli_uppercases_extension(tmp_path):
    (tmp_path / "scan.pdf").write_text("x")
    assert main([r"\.(pdf)$", r".\U\1", str(tmp_path), "--apply"]) == 0
    assert [p.name for p in tmp_path.iterdir()] == ["scan.PDF"]
