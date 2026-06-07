# SACO — Single Archive Code Output

Pack a directory tree into a single structured Markdown file.  
Zero external dependencies (stdlib only).

## Usage

```bash
python saco.py [-o output.md] [-i pattern] [--root dir] [--no-gitignore] [-v]
```

Default output: `saco_output.md`.

| Flag | Description |
|---|---|
| `-o` | Output filename (default: `saco_output.md`) |
| `-i` | Extra ignore pattern (repeatable) |
| `--root` | Directory to scan (default: `.`) |
| `--no-gitignore` | Ignore `.gitignore` rules |
| `-v` | Print filenames as they're processed |

The output is automatically excluded from the scan — no self-reading loops.  
If `.gitignore` doesn't exist, it's created with the default output name. If it
exists, the name is appended if not already present.

## What it does

1. Walks a directory tree
2. Filters files (built-in ignores + `.gitignore` + CLI patterns + binary detection)
3. Produces a single Markdown file with a directory tree and per-file code blocks

## Limitations

- Binaries (images, videos, archives, compiled objects) are detected by extension
  and null-byte scan — they're excluded from the output.
- Symlinks are always skipped.
- Files are read with `errors='replace'` — invalid bytes become `�`.
- No tests, no linter, no install step. Drop the file and run it.
