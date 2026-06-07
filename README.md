# SACO — Single Archive Code Output

Pack a directory tree into a single structured Markdown file.  
Zero external dependencies (stdlib only).

## Usage

```bash
python saco.py [-o output.md] [-i pattern[,pattern]] [-r] [-l ".ext:lang"] [--replace-lang]
               [--eject {local,global}] [--priority {local,global}] [--root dir]
               [--no-gitignore] [-v] [--force]
```

Default output: `saco_output.md`.

| Flag | Description |
|---|---|
| `-o` | Output filename (default: `saco_output.md`) |
| `-i` | Extra ignore patterns, comma-separated (`-i "*.log, tmp/"`) |
| `-r` | Discard built-in ignores, `.gitignore`, and `.saco/ignore.txt` |
| `-l` | Inject/override a language mapping (`-l ".py:python3"`, repeatable) |
| `--replace-lang` | Clear all language mappings; only `-l` entries apply |
| `--eject` | Generate `.saco/` config directory (`local` or `global`) |
| `--priority` | Config cascade order: `local` (default) or `global` |
| `--root` | Directory to scan (default: `.`) |
| `--no-gitignore` | Ignore `.gitignore` rules |
| `--force` | Allow overwriting existing `.saco/` on `--eject` |
| `-v` | Print filenames as they're processed |

## Configuration cascade

Settings are resolved from four levels (highest priority first):

1. **CLI flags** — always wins
2. **Local `.saco/`** — in current working directory
3. **Global `.saco/`** — beside `saco.py`
4. **Built-in constants** — `BUILTIN_IGNORE` and `LANG_MAP` in source

Use `--priority global` to reverse local ↔ global order.  
Run `--eject local` (or `global`) to create a `.saco/` directory with editable
`ignore.txt` and `languages.txt` files.

## What it does

1. Walks a directory tree
2. Filters files (built-in ignores + `.gitignore` + `.saco/ignore.txt` + CLI + binary detection)
3. Produces a single Markdown file with a directory tree and per-file code blocks

The output is automatically excluded from the scan — no self-reading loops.  
If `.gitignore` doesn't exist, it's created with the default output name. If it
exists, the name is appended if not already present.

## Limitations

- Binaries (images, videos, archives, compiled objects) are detected by extension
  and null-byte scan — they're excluded from the output.
- Symlinks are always skipped.
- Files are read with `errors='replace'` — invalid bytes become `�`.
- No tests, no linter, no install step. Drop the file and run it.
