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


def find_python_files(repository_path: str) -> list[Path]:
    """
    Find valid Python source files in a repository.

    Ignores:
    - virtual environments
    - dependency folders
    - cache/generated folders
    - .git
    - Python files larger than 1 MB
    """

    root = Path(repository_path)
    python_files = []

    for path in root.rglob("*.py"):

        # Ignore files inside unwanted directories
        if any(part in IGNORED_DIRECTORIES for part in path.parts):
            continue

        # Ignore files larger than 1 MB
        if path.stat().st_size > MAX_FILE_SIZE:
            continue

        python_files.append(path)

    return python_files