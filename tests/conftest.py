import pytest


@pytest.fixture(autouse=True)
def isolated_state(tmp_path_factory, monkeypatch):
    """Keep the undo journal out of the real home directory during tests."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("state")))
