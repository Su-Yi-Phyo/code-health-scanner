"""
dead_code.py — Universal dead-code detector via tree-sitter.

Extracts top-level definition names (functions, classes, methods) from the
parse tree of every file, then checks whether each name appears anywhere
else in the repository.  A name whose only occurrence is its own definition
is flagged as potentially dead code.

Works for any language supported by the tree-sitter parser layer because it
relies on a shared set of node-type names that most grammars use.

Public API
----------
detect_dead_code(files, parse_results) -> dict[str, list[DeadCodeIssue]]

    files          : list[Path] — all source files
    parse_results  : dict[str, ParseResult] — keyed by str(path)
    returns        : mapping file-path-string → list of DeadCodeIssue dicts

DeadCodeIssue schema
--------------------
{
    "name"       : str,                         # identifier name
    "kind"       : "function" | "class" | "method",
    "line_start" : int,
    "line_end"   : int,
}
"""

from __future__ import annotations

from pathlib import Path

from scoring_agent.parser import ParseResult


# ---------------------------------------------------------------------------
# Node types considered "definitions" across tree-sitter grammars
# ---------------------------------------------------------------------------
_FUNCTION_NODE_TYPES: frozenset[str] = frozenset({
    "function_definition",     # Python, C, C++, Rust, Go, Ruby …
    "function_declaration",    # JavaScript, TypeScript, C, C++ …
    "method_definition",       # JavaScript / TypeScript class body
    "method_declaration",      # Java, C#, Kotlin …
    "func_literal",            # Go anonymous but named via assignment
    "function_item",           # Rust
    "def",                     # some grammars use bare "def"
})

_CLASS_NODE_TYPES: frozenset[str] = frozenset({
    "class_definition",        # Python, Ruby
    "class_declaration",       # JavaScript, TypeScript, Java, C#, Kotlin …
    "class_specifier",         # C++
    "struct_item",             # Rust
    "type_declaration",        # Go (covers structs / interfaces)
    "interface_declaration",   # Java, TypeScript
})

# Attribute names that hold the identifier node inside a definition node
_NAME_FIELD_NAMES: tuple[str, ...] = ("name",)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_name(node) -> str | None:
    """
    Extract the identifier name from a definition node.
    Tries the 'name' child field first, then searches direct children for an
    'identifier' node.
    """
    # tree-sitter child_by_field_name
    for field in _NAME_FIELD_NAMES:
        child = node.child_by_field_name(field)
        if child is not None:
            return child.text.decode("utf-8", errors="replace")

    # Fallback: first direct child that is an identifier
    for child in node.children:
        if child.type == "identifier":
            return child.text.decode("utf-8", errors="replace")

    return None


def _collect_definitions(root_node, source_lines: list[str]) -> list[dict]:
    """
    Walk *root_node* (a tree-sitter Node) and collect all function / class
    definitions with their name, kind, and line range.

    Only top-level and one level of nesting (methods inside classes) are
    collected; deeply nested helpers are intentionally skipped to reduce
    noise.
    """
    definitions: list[dict] = []
    if root_node is None:
        return definitions

    def _visit(node, depth: int) -> None:
        if depth > 4:          # guard against runaway recursion
            return

        node_type = node.type

        if node_type in _FUNCTION_NODE_TYPES:
            name = _get_name(node)
            if name:
                kind = "method" if depth > 1 else "function"
                definitions.append({
                    "name": name,
                    "kind": kind,
                    "line_start": node.start_point[0] + 1,   # 0-based → 1-based
                    "line_end":   node.end_point[0]   + 1,
                })
            # Still recurse to catch nested classes
            for child in node.children:
                _visit(child, depth + 1)

        elif node_type in _CLASS_NODE_TYPES:
            name = _get_name(node)
            if name:
                definitions.append({
                    "name": name,
                    "kind": "class",
                    "line_start": node.start_point[0] + 1,
                    "line_end":   node.end_point[0]   + 1,
                })
            # Recurse into class body to pick up methods
            for child in node.children:
                _visit(child, depth + 1)

        else:
            for child in node.children:
                _visit(child, depth + 1)

    _visit(root_node, depth=0)
    return definitions


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_dead_code(
    files: list[Path],
    parse_results: dict[str, "ParseResult"],
) -> dict[str, list[dict]]:
    """
    Detect definitions that are never referenced outside their own file.

    Algorithm
    ---------
    1. Extract all top-level definition names from every parse tree.
    2. Build a full-text corpus (all file contents concatenated).
    3. A name is dead when its count in the corpus equals 1 (only the
       definition keyword line itself contains it).
    """
    # Step 1 — collect definitions per file
    file_defs: dict[str, list[dict]] = {}
    for path in files:
        path_str = str(path)
        pr = parse_results.get(path_str)
        if pr is None or pr.root_node is None:
            continue
        defs = _collect_definitions(pr.root_node, pr.source.splitlines())
        if defs:
            file_defs[path_str] = defs

    if not file_defs:
        return {}

    # Step 2 — build full-text corpus for reference counting
    corpus_parts: list[str] = []
    for path in files:
        pr = parse_results.get(str(path))
        if pr is not None:
            corpus_parts.append(pr.source)
    corpus = "\n".join(corpus_parts)

    # Step 3 — flag names whose count in corpus == 1
    results: dict[str, list[dict]] = {}

    for path_str, defs in file_defs.items():
        issues: list[dict] = []
        for defn in defs:
            name = defn["name"]
            # Count how many times the bare name appears in the whole corpus
            # (simple substring count — fast and language-agnostic)
            if corpus.count(name) == 1:
                issues.append(defn)
        if issues:
            results[path_str] = issues

    return results
