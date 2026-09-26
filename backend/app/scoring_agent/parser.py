"""
parser.py — Universal tree-sitter parser layer.

Uses individual `tree-sitter-*` language packages (compatible with
tree-sitter >= 0.22 / Python 3.13+) to parse any supported source file.

Each language package exposes its grammar via `<package>.language()`.
Languages without an installed package degrade gracefully — the pipeline
still returns a ParseResult with parse_error set (no crash).

Public API
----------
parse_file(file_path, language) -> ParseResult

ParseResult fields
------------------
language    : str               language name (e.g. "python", "go")
source      : str               raw source text (utf-8, errors replaced)
tree        : Tree | None       tree-sitter parse tree; None on failure
root_node   : Node | None       root of the tree; None on failure
parse_error : str | None        human-readable error if tree is None
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    _TS_CORE_AVAILABLE = True
except ImportError:
    _TS_CORE_AVAILABLE = False
    Language = None  # type: ignore[assignment,misc]
    Parser = None    # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Lazy registry: language name → callable that returns a Language object
# Each entry is tried at import time; missing packages are silently skipped.
# ---------------------------------------------------------------------------

def _try_import(module: str, func: str = "language"):
    """
    Return a callable that produces a tree_sitter.Language object, or None
    if the package is not installed or the grammar fails to load.

    tree-sitter >= 0.22 expects Parser(Language(capsule)); earlier versions
    accepted the raw capsule directly.  We always wrap in Language() here.
    """
    try:
        import importlib
        mod = importlib.import_module(module)
        fn = getattr(mod, func)
        capsule = fn()
        # Verify wrapping works before registering
        Language(capsule)
        return lambda: Language(fn())
    except Exception:  # noqa: BLE001
        return None


_LANGUAGE_LOADERS: dict[str, object] = {}

_CANDIDATES = [
    ("python",      "tree_sitter_python"),
    ("javascript",  "tree_sitter_javascript"),
    ("typescript",  "tree_sitter_typescript"),
    ("tsx",         "tree_sitter_typescript", "language_tsx"),
    ("html",        "tree_sitter_html"),
    ("css",         "tree_sitter_css"),
    ("java",        "tree_sitter_java"),
    ("kotlin",      "tree_sitter_kotlin"),
    ("scala",       "tree_sitter_scala"),
    ("c",           "tree_sitter_c"),
    ("cpp",         "tree_sitter_cpp"),
    ("c_sharp",     "tree_sitter_c_sharp"),
    ("rust",        "tree_sitter_rust"),
    ("go",          "tree_sitter_go"),
    ("ruby",        "tree_sitter_ruby"),
    ("php",         "tree_sitter_php"),
    ("lua",         "tree_sitter_lua"),
    ("r",           "tree_sitter_r"),
    ("bash",        "tree_sitter_bash"),
    ("haskell",     "tree_sitter_haskell"),
    ("elixir",      "tree_sitter_elixir"),
    ("erlang",      "tree_sitter_erlang"),
    ("elm",         "tree_sitter_elm"),
    ("ocaml",       "tree_sitter_ocaml"),
    ("json",        "tree_sitter_json"),
    ("toml",        "tree_sitter_toml"),
    ("yaml",        "tree_sitter_yaml"),
    ("sql",         "tree_sitter_sql"),
    ("swift",       "tree_sitter_swift"),
    ("dart",        "tree_sitter_dart"),
    ("julia",       "tree_sitter_julia"),
    ("nim",         "tree_sitter_nim"),
    ("zig",         "tree_sitter_zig"),
]

for _entry in _CANDIDATES:
    if len(_entry) == 2:
        _lang_name, _module = _entry
        _func = "language"
    else:
        _lang_name, _module, _func = _entry
    _loader = _try_import(_module, _func)
    if _loader is not None:
        _LANGUAGE_LOADERS[_lang_name] = _loader


# ---------------------------------------------------------------------------
# ParseResult
# ---------------------------------------------------------------------------

@dataclass
class ParseResult:
    language: str
    source: str
    tree: object = field(default=None)       # tree_sitter.Tree
    root_node: object = field(default=None)  # tree_sitter.Node
    parse_error: str | None = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_file(file_path: str | Path, language: str) -> ParseResult:
    """
    Parse *file_path* with the tree-sitter grammar for *language*.

    Returns a ParseResult.  On any failure (missing grammar, parse error)
    ``parse_error`` is set and ``tree`` / ``root_node`` are None.
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8", errors="replace")

    if not _TS_CORE_AVAILABLE:
        return ParseResult(
            language=language,
            source=source,
            parse_error=(
                "tree-sitter core is not installed. "
                "Run: pip install tree-sitter>=0.22"
            ),
        )

    loader = _LANGUAGE_LOADERS.get(language)
    if loader is None:
        return ParseResult(
            language=language,
            source=source,
            parse_error=f"No tree-sitter grammar available for language '{language}'.",
        )

    try:
        lang_obj = loader()
        parser = Parser(lang_obj)
        tree = parser.parse(source.encode("utf-8", errors="replace"))
        return ParseResult(
            language=language,
            source=source,
            tree=tree,
            root_node=tree.root_node,
        )
    except Exception as exc:  # noqa: BLE001
        return ParseResult(
            language=language,
            source=source,
            parse_error=f"tree-sitter parse error: {exc}",
        )


def supported_languages() -> list[str]:
    """Return a list of language names with an available grammar."""
    return sorted(_LANGUAGE_LOADERS.keys())
