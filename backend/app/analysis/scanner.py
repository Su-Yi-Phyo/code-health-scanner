from pathlib import Path


IGNORED_DIRECTORIES = {
    ".venv",
    "venv",
    "__pycache__",
    "site-packages",
    "node_modules",
    "dist",
    "build",
    ".git",
}

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

# Maps file extension → language name used throughout the pipeline.
# Covers the ~40 languages supported by tree-sitter-languages.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    # Python
    ".py": "python",
    # JavaScript / TypeScript
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    # JVM
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    # C-family
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".cs": "c_sharp",
    # Systems
    ".rs": "rust",
    ".go": "go",
    # Scripting
    ".rb": "ruby",
    ".php": "php",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
    # Shell
    ".sh": "bash",
    ".bash": "bash",
    # Functional
    ".hs": "haskell",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".elm": "elm",
    ".ml": "ocaml",
    ".mli": "ocaml",
    # Data / Config
    ".json": "json",
    ".toml": "toml",
    ".yaml": "yaml",
    ".yml": "yaml",
    # Query
    ".sql": "sql",
    # Mobile / Apple
    ".swift": "swift",
    # Other
    ".dart": "dart",
    ".jl": "julia",
    ".nim": "nim",
    ".zig": "zig",
}


def find_source_files(
    repository_path: str,
    extensions: set[str] | None = None,
) -> list[Path]:
    """
    Find all source files in a repository for supported languages.

    Parameters
    ----------
    repository_path:
        Local path to the extracted repository root.
    extensions:
        Optional explicit set of file extensions to include (e.g. {".py", ".js"}).
        Defaults to all keys in SUPPORTED_EXTENSIONS.

    Ignores:
    - Virtual-environment / dependency / cache folders
    - .git
    - Files larger than 1 MB
    """
    allowed = extensions if extensions is not None else set(SUPPORTED_EXTENSIONS.keys())
    root = Path(repository_path)
    source_files: list[Path] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        # Ignore files inside unwanted directories
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        # Only include files with a supported extension
        if path.suffix not in allowed:
            continue

        # Ignore files larger than 1 MB
        if path.stat().st_size > MAX_FILE_SIZE:
            continue

        source_files.append(path)

    return source_files


def get_language(file_path: Path) -> str:
    """Return the language name for a given file path, or 'unknown'."""
    return SUPPORTED_EXTENSIONS.get(file_path.suffix, "unknown")


# ---------------------------------------------------------------------------
# Backwards-compatibility alias
# ---------------------------------------------------------------------------

def find_python_files(repository_path: str) -> list[Path]:
    """Backwards-compatible alias — returns only Python (.py) files."""
    return find_source_files(repository_path, extensions={".py"})
