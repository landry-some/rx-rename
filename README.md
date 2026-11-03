# rx-rename

A command-line tool for renaming many files at once with a regular expression. It
shows every old → new name, and any collisions, before anything on disk changes.

It's for people who tidy folders of downloads, photos or scans from the terminal and
don't want to write a one-off shell loop that turns out to be wrong halfway through.

Built with Python 3.11+ and the standard library only. Tests use pytest.

## Status

Early development. See [ROADMAP.md](ROADMAP.md) for what v0.1 covers and what comes next.

## Install

```bash
git clone https://github.com/landry-some/rx-rename.git
cd rx-rename
python3 -m venv .venv
.venv/bin/pip install -e .
```

## Test

```bash
.venv/bin/pip install pytest
.venv/bin/pytest
```

## License

MIT, see [LICENSE](LICENSE).
