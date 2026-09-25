"""
ast_analyzer.py – Phase 1: Python source-file structure extraction.

Parses a .py file with the standard-library `ast` module (no execution) and
returns a plain dictionary that can be serialised directly to JSON.

Schema returned by `analyze_file`:
{
    "file_path":   str,
    "line_count":  int,
    "syntax_error": str | None,       # non-None when parsing failed
    "imports":     [
        {
            "type":   "import" | "from_import",
            "module": str,            # "os.path", "pathlib", …
            "names":  [str],          # imported names / aliases
            "line":   int,
        }, …
    ],
    "functions":   [ <FunctionInfo>, … ],   # top-level only
    "classes":     [ <ClassInfo>,    … ],
}

FunctionInfo:
{
    "name":         str,
    "line_start":   int,
    "line_end":     int,
    "decorators":   [str],
    "nested_functions": [ <FunctionInfo>, … ],
    "nested_classes":   [ <ClassInfo>,   … ],
}

ClassInfo:
{
    "name":         str,
    "line_start":   int,
    "line_end":     int,
    "decorators":   [str],
    "methods":      [ <FunctionInfo>, … ],
    "nested_classes":   [ <ClassInfo>, … ],
}
"""

import ast
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    """Return a list of decorator name strings for a function/class node."""
    names = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.append(ast.unparse(dec))
        elif isinstance(dec, ast.Call):
            names.append(ast.unparse(dec))
        else:
            names.append(ast.unparse(dec))
    return names


def _end_line(node: ast.AST) -> int:
    """Return the last line number of an AST node."""
    return getattr(node, "end_lineno", node.lineno)


def _extract_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict:
    """Recursively build a FunctionInfo dict from a function/async-function node."""
    nested_functions = []
    nested_classes = []

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nested_functions.append(_extract_function(child))
        elif isinstance(child, ast.ClassDef):
            nested_classes.append(_extract_class(child))

    return {
        "name": node.name,
        "line_start": node.lineno,
        "line_end": _end_line(node),
        "decorators": _decorator_names(node),
        "nested_functions": nested_functions,
        "nested_classes": nested_classes,
    }


def _extract_class(node: ast.ClassDef) -> dict:
    """Recursively build a ClassInfo dict from a class node."""
    methods = []
    nested_classes = []

    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(_extract_function(child))
        elif isinstance(child, ast.ClassDef):
            nested_classes.append(_extract_class(child))

    return {
        "name": node.name,
        "line_start": node.lineno,
        "line_end": _end_line(node),
        "decorators": _decorator_names(node),
        "methods": methods,
        "nested_classes": nested_classes,
    }


def _extract_imports(tree: ast.Module) -> list[dict]:
    """Walk top-level import statements and return structured import records."""
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "type": "import",
                    "module": alias.name,
                    "names": [alias.asname or alias.name],
                    "line": node.lineno,
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.asname or alias.name for alias in node.names]
            imports.append({
                "type": "from_import",
                "module": module,
                "names": names,
                "line": node.lineno,
            })

    # Preserve original source order
    imports.sort(key=lambda i: i["line"])
    return imports


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_file(file_path: str | Path) -> dict:
    """
    Analyze a single Python source file and return a structured dictionary.

    Syntax errors are caught and stored in ``result["syntax_error"]`` so that
    one broken file does not abort an entire repository scan.
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8", errors="replace")
    line_count = source.count("\n") + (1 if source else 0)

    result = {
        "file_path": str(path),
        "line_count": line_count,
        "syntax_error": None,
        "imports": [],
        "functions": [],
        "classes": [],
    }

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        result["syntax_error"] = f"{exc.msg} (line {exc.lineno})"
        return result

    result["imports"] = _extract_imports(tree)

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append(_extract_function(node))
        elif isinstance(node, ast.ClassDef):
            result["classes"].append(_extract_class(node))

    return result
