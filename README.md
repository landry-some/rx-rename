# rx-rename

A command-line tool for renaming many files at once with a regular expression. It
shows every old → new name, and any collisions, before anything on disk changes.

It's for people who tidy folders of downloads, photos or scans from the terminal and
don't want to write a one-off shell loop that turns out to be wrong halfway through.

Built with Python 3.11+ and the standard library only. Tests use pytest.

## Status

v0.1. See [ROADMAP.md](ROADMAP.md) for what comes next.

## Install

```bash
git clone https://github.com/landry-some/rx-rename.git
cd rx-rename
python3 -m venv .venv
.venv/bin/pip install -e .
```

Or run it without installing: `PYTHONPATH=src python3 -m rx_rename.cli ...`

## Usage

```
rx-rename PATTERN REPLACEMENT [PATHS...] [--apply] [-r] [--glob GLOB] [--dirs] [-i]
rx-rename undo [--apply]
```

`PATTERN` is a Python regular expression matched against each file's basename (never
the directory part). `REPLACEMENT` can refer to groups with `\1` or `\g<name>`. `PATHS`
default to the current directory. Quote both arguments so the shell leaves them alone.

`\U`, `\L` and `\T` in `REPLACEMENT` upper-, lower- or title-case everything after them
(group text included) up to `\E` or the next of these escapes. For example
`'\.(jpe?g)$' '.\U\1'` turns `cat.jpg` into `cat.JPG`, and `'^(.*)$' '\T\1'` turns
`summer holiday.mp4` into `Summer Holiday.Mp4`. Write `\\U` for a literal `\U`.

`REPLACEMENT` can also contain these tokens:

- `{n}` the number of this rename in the batch, from 1, in the order files are listed
  (sorted by name within each directory). Add a format spec to pad it: `{n:03}` → `007`.
- `{mtime}` the file's modification date as `2024-03-09`, or any `strftime` format such
  as `{mtime:%Y%m%d-%H%M}`.

So `'^IMG_\d+' '{mtime}-{n:03}'` turns `IMG_4711.jpg` into `2024-03-09-001.jpg`. Other
braces are kept as they are.

Without `--apply` nothing on disk changes. Using the fake files in `examples/photos/`:

```console
$ rx-rename -i 'IMG_(\d+)\.jpg' 'beach-\1.jpg' examples/photos
examples/photos/IMG_0001.JPG  ->  examples/photos/beach-0001.jpg
examples/photos/IMG_0002.JPG  ->  examples/photos/beach-0002.jpg
examples/photos/IMG_0003.jpg  ->  examples/photos/beach-0003.jpg

3 file(s) would be renamed. Nothing was changed.
Run again with --apply to rename them.
```

Add `--apply` to do it. Renames go through temporary names first, so swaps and
cycles such as `a → b, b → a` work. If any rename fails, the ones already done are
put back.

### Conflicts

These block `--apply` and are shown with `!!` in the preview:

- two files would get the same new name
- the new name already exists (and isn't being renamed away in the same batch)
- the new name is empty, `.`, `..`, or contains `/`
- a file sits inside a directory that is also being renamed (`-r --dirs`)

### Options

| Option | Effect |
|---|---|
| `--apply` | Actually rename. |
| `-r`, `--recursive` | Descend into subdirectories of directory arguments. |
| `--glob GLOB` | Only consider names matching `GLOB`, e.g. `'*.jpg'`. Files named directly on the command line are always considered. |
| `--dirs` | Rename directories too, not just files. |
| `-i`, `--ignore-case` | Case-insensitive pattern. |

### Undo

Every `--apply` saves the batch to `$XDG_STATE_HOME/rx-rename/last.json`
(`~/.local/state/rx-rename/last.json` by default). `rx-rename undo` previews reversing
it and `rx-rename undo --apply` does it. Undo refuses if a renamed file has since moved
or if something new now has one of the original names. Only the most recent batch is
kept.

### Exit codes

`0` success or nothing to do, `1` conflicts or a failed rename, `2` bad pattern,
replacement, path or journal.

## Test

```bash
.venv/bin/pip install pytest
.venv/bin/pytest
```

## License

MIT, see [LICENSE](LICENSE).
