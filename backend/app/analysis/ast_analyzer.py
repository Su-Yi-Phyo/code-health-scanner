"""
ast_analyzer.py — Retained for backwards compatibility only.

All language analysis is now handled universally by the scoring_agent
package (tree-sitter parser + detectors + scorer).  This module is no
longer called by the main pipeline; it exists solely so that existing
test_ast_analyzer.py imports do not break.

The public function `analyze_file` is kept with the same signature but
now delegates entirely to the scoring_agent parser layer and returns a
minimal dict.  The Python-specific fields (imports, functions, classes)
are no longer populated — use the scoring_agent directly for analysis.
"""

import sys
from pathlib import Path

# Make scoring_agent importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring_agent.parser import parse_file as _parse_file   # noqa: E402
from analysis.scanner import get_language                     # noqa: E402


def analyze_file(file_path: str | Path, language: str | None = None) -> dict:
    """
    Analyze a single source file and return a minimal structured dictionary.

    Language-specific AST extraction (Python imports/functions/classes) has
    been removed in favour of the universal scoring_agent pipeline.

    Returned schema
    ---------------
    {
        "file_path":    str,
        "language":     str,
        "line_count":   int,
        "parse_error":  str | None,
    }
    """
    path = Path(file_path)
    if language is None:
        language = get_language(path)

    pr = _parse_file(path, language)
    line_count = pr.source.count("\n") + (1 if pr.source else 0)

    return {
        "file_path":   str(path),
        "language":    language,
        "line_count":  line_count,
        "parse_error": pr.parse_error,
    }
