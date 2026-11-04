# Roadmap

## v0.1

- [x] Preview by default: `rx-rename PATTERN REPLACEMENT [PATHS...]` prints old → new, changes nothing
- [x] Conflict checks: duplicate targets, existing targets, empty/invalid names block `--apply`
- [x] `--apply` with two-phase renames so swaps and cycles work
- [x] Selection: `-r` recursive, `--glob` filter, `--dirs` to include directories, `-i` ignore case
- [x] Undo: JSON journal per apply, `rx-rename undo` reverses the last batch

## After v0.1 (~29 h)

### Features (13 h)
- [x] Counter/sequence tokens (`{n:03}`) and date-from-mtime tokens — 3 h
- [x] Case transforms (`\U`, `\L`, title case) in the replacement — 2 h
- [ ] Interactive mode: approve or skip each rename — 2.5 h
- [ ] Coloured highlighting of the changed part of each name — 2 h
- [ ] Option to match against the relative path, not just the basename — 1.5 h
- [x] Undo history beyond the last batch (`undo --list`, `undo <id>`) — 2 h

### Bugs and edge cases (8 h)
- [ ] Case-only renames on case-insensitive filesystems (macOS, Windows) — 2 h
- [ ] Symlinks, hidden files, permission errors, rollback on partial failure — 2.5 h
- [ ] Unicode normalisation (NFC/NFD) and per-OS invalid filename characters — 2 h
- [ ] Renaming a directory and its contents in the same batch — 1.5 h

### Refactors (3 h)
- [ ] Keep the planner pure and the executor the only I/O layer as features grow — 2 h
- [ ] Version the journal format — 1 h

### Tests (3 h)
- [ ] Property-style tests for swap/cycle planning — 1.5 h
- [ ] CI on Linux, macOS and Windows with GitHub Actions — 1.5 h

### Docs (2.5 h)
- [ ] README cookbook of common regex recipes — 1.5 h
- [ ] Richer `--help` examples and a CHANGELOG — 1 h
