#!/usr/bin/env python3
import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BUILTIN_IGNORE = [
    '.git/',
    '__pycache__/',
    'venv/',
    '.opencode/',
    '*.pyc',
    '*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.ico', '*.svg',
    '*.pdf', '*.pyd', '*.so', '*.dll', '*.dylib',
    '*.bin', '*.exe', '*.zip', '*.tar', '*.gz', '*.rar', '*.7z',
    '*.o', '*.a', '*.lib', '*.class', '*.whl',
    '*.ttf', '*.otf', '*.woff', '*.woff2', '*.eot',
    '*.mp3', '*.mp4', '*.avi', '*.mov', '*.mkv',
    '*.iso', '*.img',
]

LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.jsx': 'jsx',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.rs': 'rust',
    '.go': 'go',
    '.rb': 'ruby',
    '.java': 'java',
    '.kt': 'kotlin',
    '.kts': 'kotlin',
    '.scala': 'scala',
    '.swift': 'swift',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.cs': 'csharp',
    '.fs': 'fsharp',
    '.php': 'php',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'bash',
    '.fish': 'fish',
    '.ps1': 'powershell',
    '.bat': 'batch',
    '.cmd': 'batch',
    '.pl': 'perl',
    '.pm': 'perl',
    '.lua': 'lua',
    '.r': 'r',
    '.m': 'matlab',
    '.hs': 'haskell',
    '.clj': 'clojure',
    '.cljs': 'clojure',
    '.ex': 'elixir',
    '.exs': 'elixir',
    '.erl': 'erlang',
    '.vim': 'viml',
    '.lisp': 'lisp',
    '.scm': 'scheme',
    '.ml': 'ocaml',
    '.elm': 'elm',
    '.sql': 'sql',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'conf',
    '.md': 'markdown',
    '.rst': 'rst',
    '.tex': 'latex',
    '.dockerfile': 'dockerfile',
    '.makefile': 'makefile',
    '.cmake': 'cmake',
    '.gradle': 'gradle',
    '.tf': 'terraform',
    '.tfvars': 'terraform',
    '.zig': 'zig',
    '.nim': 'nim',
    '.dart': 'dart',
    '.vue': 'vue',
    '.svelte': 'svelte',
    '.astro': 'astro',
    '.graphql': 'graphql',
    '.gql': 'graphql',
    '.proto': 'protobuf',
    '.sol': 'solidity',
    '.coffee': 'coffeescript',
}

DEFAULT_OUTPUT = 'saco_output.md'


def parse_args():
    parser = argparse.ArgumentParser(
        description='SACO — Single Archive Code Output')
    parser.add_argument('-o', '--output', default=DEFAULT_OUTPUT,
                        help=f'archivo de salida (default: {DEFAULT_OUTPUT})')
    parser.add_argument('-i', '--ignore', action='append', default=[],
                        help='patrón adicional (comma-separated: -i "*.log, tmp/")')
    parser.add_argument('-r', '--replace-ignore', action='store_true',
                        help='descarta built-ins, .gitignore y .saco/ignore.txt')
    parser.add_argument('-l', '--lang', action='append', default=[],
                        help='inyecta/sobrescribe extensión (.py:python3)')
    parser.add_argument('--replace-lang', action='store_true',
                        help='vacía LANG_MAP entero, solo usa -l')
    parser.add_argument('--eject', choices=['local', 'global'], default=None,
                        help='crea .saco/ en cwd (local) o junto al script (global)')
    parser.add_argument('--priority', choices=['local', 'global'], default='local',
                        help='invierte prioridad local↔global (default: local)')
    parser.add_argument('--root', default='.',
                        help='directorio raíz a escanear (default: .)')
    parser.add_argument('--no-gitignore', action='store_true',
                        help='ignorar .gitignore del proyecto')
    parser.add_argument('--force', action='store_true',
                        help='permite sobrescribir .saco/ existente en --eject')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='mostrar progreso en stderr')
    return parser.parse_args()


def eject_config(target_dir: Path, force: bool):
    saco_dir = target_dir / '.saco'
    if saco_dir.exists() and not force:
        print(f'Error: {saco_dir} already exists. Use --force to overwrite.',
              file=sys.stderr)
        sys.exit(1)
    saco_dir.mkdir(parents=True, exist_ok=True)

    with open(saco_dir / 'ignore.txt', 'w') as f:
        for pattern in BUILTIN_IGNORE:
            f.write(pattern + '\n')

    with open(saco_dir / 'languages.txt', 'w') as f:
        for ext, lang in sorted(LANG_MAP.items()):
            f.write(f'{ext}:{lang}\n')

    print(f'[saco] configuration ejected to {saco_dir}', file=sys.stderr)
    sys.exit(0)


def ensure_output_is_ignored(output_name: str):
    gitignore = Path('.gitignore')
    target = output_name + '\n'

    if not gitignore.exists():
        gitignore.write_text(target)
        return

    found = False
    with gitignore.open('r', errors='replace') as f:
        for line in f:
            if line.rstrip() == output_name:
                found = True
                break

    if not found:
        with gitignore.open('a') as f:
            f.write(target)


def load_gitignore_patterns(root: Path):
    gitignore = root / '.gitignore'
    if not gitignore.exists():
        return []
    lines = []
    with gitignore.open('r', errors='replace') as f:
        for line in f:
            lines.append(line.rstrip('\n'))
    return lines


def load_ignore_file(path: Path):
    lines = []
    with path.open('r', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
    return lines


def load_languages_file(path: Path):
    mapping = {}
    with path.open('r', errors='replace') as f:
        for line in f:
            stripped = line.strip()
            if stripped and ':' in stripped:
                ext, lang = stripped.split(':', 1)
                mapping[ext.strip()] = lang.strip()
    return mapping


def load_config_cascade(args, script_dir):
    cwd_saco = Path.cwd() / '.saco'
    script_saco = script_dir / '.saco'

    if args.priority == 'global':
        primary, secondary = script_saco, cwd_saco
        primary_name, secondary_name = 'global', 'local'
    else:
        primary, secondary = cwd_saco, script_saco
        primary_name, secondary_name = 'local', 'global'

    file_ignore_patterns = []
    for d, name in [(primary, primary_name), (secondary, secondary_name)]:
        ignore_file = d / 'ignore.txt'
        if ignore_file.exists():
            file_ignore_patterns = load_ignore_file(ignore_file)
            print(f'[saco] using ignore.txt from .saco/ ({name})',
                  file=sys.stderr)
            break

    file_lang_map = {}
    for d, name in [(primary, primary_name), (secondary, secondary_name)]:
        lang_file = d / 'languages.txt'
        if lang_file.exists():
            file_lang_map = load_languages_file(lang_file)
            print(f'[saco] using languages.txt from .saco/ ({name})',
                  file=sys.stderr)
            break

    return file_ignore_patterns, file_lang_map


def parse_gitignore_line(raw_line: str):
    line = raw_line.rstrip()

    if not line or line.startswith('#'):
        return None

    negate = False
    if line.startswith('!'):
        negate = True
        line = line[1:]

    dir_only = False
    if line.endswith('/'):
        dir_only = True
        line = line[:-1]

    if not line:
        return None

    anchored = '/' in line

    return {
        'pattern': line,
        'negate': negate,
        'dir_only': dir_only,
        'anchored': anchored,
    }


def _gitignore_to_regex(pattern: str, anchored: bool, dir_only: bool):
    result = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                if i + 2 < len(pattern) and pattern[i + 2] == '/':
                    result.append('(.*/)?')
                    i += 3
                else:
                    result.append('.*')
                    i += 2
            else:
                result.append('[^/]*')
                i += 1
        elif c == '?':
            result.append('[^/]')
            i += 1
        elif c == '[':
            j = i + 1
            if j < len(pattern) and pattern[j] == '!':
                j += 1
            if j < len(pattern) and pattern[j] == ']':
                j += 1
            while j < len(pattern) and pattern[j] != ']':
                if pattern[j] == '\\':
                    j += 1
                j += 1
            if j >= len(pattern):
                j = len(pattern)
            else:
                j += 1
            result.append(pattern[i:j])
            i = j
        else:
            if c in '.^$()+{}|\\':
                result.append('\\' + c)
            else:
                result.append(c)
            i += 1

    regex = ''.join(result)

    if not anchored:
        regex = '(.*/)?' + regex

    if dir_only:
        regex = regex + '(/.*)?'

    return re.compile('^' + regex + '$')


def compile_ignore_patterns(builtins, gitignore_raw, file_ignore_patterns,
                            cli_patterns, output_name, replace_ignore=False):
    all_patterns = []

    if not replace_ignore:
        for p in builtins:
            parsed = parse_gitignore_line(p)
            if parsed:
                all_patterns.append(parsed)

        for line in gitignore_raw:
            parsed = parse_gitignore_line(line)
            if parsed:
                all_patterns.append(parsed)

        for p in file_ignore_patterns:
            parsed = parse_gitignore_line(p)
            if parsed:
                all_patterns.append(parsed)

    for p in cli_patterns:
        parsed = parse_gitignore_line(p)
        if parsed:
            all_patterns.append(parsed)

    parsed = parse_gitignore_line(output_name)
    if parsed:
        all_patterns.append(parsed)

    compiled = []
    for p in all_patterns:
        regex = _gitignore_to_regex(p['pattern'], p['anchored'], p['dir_only'])
        compiled.append((regex, p['negate']))

    return compiled


def should_ignore(path: Path, root: Path, patterns: list):
    rel = path.relative_to(root).as_posix()
    if rel == '.':
        return False

    result = False
    for regex, negate in patterns:
        if regex.search(rel):
            result = not negate

    return result


def is_binary(path: Path):
    BINARY_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.pyc', '.pyd', '.so', '.dll', '.dylib',
        '.bin', '.exe', '.zip', '.tar', '.gz', '.rar', '.7z',
        '.o', '.a', '.lib', '.class', '.whl',
        '.ttf', '.otf', '.woff', '.woff2', '.eot',
        '.mp3', '.mp4', '.avi', '.mov', '.mkv',
        '.iso', '.img',
    }
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with path.open('rb') as f:
            header = f.read(1024)
        return b'\x00' in header
    except OSError:
        return True


def collect_file_paths(root: Path, patterns: list):
    sort_key = lambda p: str(p.relative_to(root)).lower()
    for path in sorted(root.rglob('*'), key=sort_key):
        if path.is_symlink() or not path.is_file():
            continue
        if should_ignore(path, root, patterns):
            continue
        if is_binary(path):
            continue
        yield path


def detect_language(suffix: str, lang_map: dict):
    return lang_map.get(suffix.lower(), '')


def stream_file_content(f_out, path: Path, chunk_size=65536):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as src:
            while chunk := src.read(chunk_size):
                f_out.write(chunk)
    except (IOError, OSError) as e:
        f_out.write(f'[Error leyendo {path.name}: {e}]\n')


def format_size(size: int):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{size:.1f} TB'


def write_header(f_out, root: Path, paths: list, total_size: int):
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    f_out.write('# SACO — Single Archive Code Output\n\n')
    f_out.write(f'Generado: {now}\n')
    f_out.write(f'Raíz: {root.resolve()}\n')
    f_out.write(f'Total archivos: {len(paths)} | Tamaño total: {format_size(total_size)}\n\n')


def write_directory_tree(f_out, root: Path, paths: list):
    f_out.write('## Árbol del proyecto\n\n')

    if not paths:
        f_out.write('*(sin archivos para empaquetar)*\n\n---\n\n')
        return

    dirs = set()
    for path in paths:
        parent = path.parent
        while parent != root:
            dirs.add(parent)
            parent = parent.parent

    tree = {}
    for d in dirs:
        node = tree
        for part in d.relative_to(root).parts:
            node = node.setdefault(part, {})
    for path in paths:
        node = tree
        for part in path.relative_to(root).parts[:-1]:
            node = node.setdefault(part, {})
        node[path.relative_to(root).parts[-1]] = None

    def render(node, prefix=''):
        items = sorted(
            node.items(),
            key=lambda x: (not isinstance(x[1], dict), x[0].lower()))
        for i, (name, value) in enumerate(items):
            is_last = i == len(items) - 1
            connector = '└── ' if is_last else '├── '
            suffix = '/' if isinstance(value, dict) else ''
            f_out.write(f'{prefix}{connector}{name}{suffix}\n')
            new_prefix = prefix + ('    ' if is_last else '│   ')
            if isinstance(value, dict):
                render(value, new_prefix)

    render(tree)
    f_out.write('\n---\n\n')


def write_file_section(f_out, path: Path, root: Path, lang_map: dict):
    rel = path.relative_to(root)
    lang = detect_language(path.suffix, lang_map)
    f_out.write(f'## {rel}\n\n')
    f_out.write(f'```{lang}\n')
    stream_file_content(f_out, path)
    f_out.write('\n```\n\n')


def write_output(root: Path, paths: list, output_path: str, verbose: bool,
                 lang_map: dict):
    total_size = sum(p.stat().st_size for p in paths)

    with open(output_path, 'w', encoding='utf-8', buffering=1) as f:
        write_header(f, root, paths, total_size)
        write_directory_tree(f, root, paths)

        for path in paths:
            if verbose:
                print(path.relative_to(root), file=sys.stderr)
            write_file_section(f, path, root, lang_map)

    if verbose:
        print(
            f'✓ Empaquetados {len(paths)} archivos '
            f'({format_size(total_size)}) en {output_path}',
            file=sys.stderr)


def main():
    args = parse_args()
    script_dir = Path(__file__).resolve().parent

    if args.eject:
        target = Path.cwd() if args.eject == 'local' else script_dir
        eject_config(target, args.force)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f'Error: el directorio {root} no existe', file=sys.stderr)
        sys.exit(1)

    ensure_output_is_ignored(DEFAULT_OUTPUT)

    file_ignore_patterns, file_lang_map = load_config_cascade(args, script_dir)

    if args.replace_lang:
        merged_lang_map = {}
    else:
        merged_lang_map = LANG_MAP.copy()
        merged_lang_map.update(file_lang_map)

    if args.lang:
        for entry in args.lang:
            if ':' in entry:
                ext, lang = entry.split(':', 1)
                merged_lang_map[ext.strip()] = lang.strip()

    gitignore_raw = load_gitignore_patterns(root) if not args.no_gitignore else []

    cli_patterns = []
    for p in args.ignore:
        cli_patterns.extend([part.strip() for part in p.split(',')])

    patterns = compile_ignore_patterns(
        BUILTIN_IGNORE, gitignore_raw, file_ignore_patterns,
        cli_patterns, args.output, args.replace_ignore)

    paths = list(collect_file_paths(root, patterns))
    write_output(root, paths, args.output, args.verbose, merged_lang_map)


if __name__ == '__main__':
    main()
