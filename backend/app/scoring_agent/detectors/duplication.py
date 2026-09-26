"""
duplication.py — Hash-based duplicate code block detector.

Works on raw source text (language-agnostic). Slides a window of
BLOCK_SIZE non-blank lines across every file; blocks whose content hash
appears in more than one location are flagged as duplicates.

Public API
----------
detect_duplicates(files) -> dict[str, list[DuplicateIssue]]

    files  : list of Path objects to scan (any language)
    returns: mapping of file-path-string → list of DuplicateIssue dicts

DuplicateIssue schema
---------------------
{
    "line_start"    : int,   # 1-based start line of the duplicate block
    "line_end"      : int,   # 1-based end line
    "duplicate_of"  : str,   # "<other_file>:<line_start>-<line_end>"
}
"""

from __future__ import annotations

import hashlib
from pathlib import Path


# Number of consecutive non-blank lines that form one "block".
BLOCK_SIZE: int = 6


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------

# One entry in the global hash index: (file_path_str, line_start, line_end)
_BlockRef = tuple[str, int, int]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _content_lines(source: str) -> list[tuple[int, str]]:
    """
    Return (original_1based_line_number, stripped_line) for every
    non-blank line in *source*.
    """
    result = []
    for lineno, raw in enumerate(source.splitlines(), start=1):
        stripped = raw.strip()
        if stripped:
            result.append((lineno, stripped))
    return result


def _hash_block(lines: list[str]) -> str:
    joined = "\n".join(lines).encode("utf-8")
    return hashlib.md5(joined).hexdigest()  # noqa: S324 — not security-critical


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_duplicates(files: list[Path]) -> dict[str, list[dict]]:
    """
    Scan *files* for duplicate code blocks and return findings per file.

    Algorithm
    ---------
    1. For each file build a list of (original_lineno, content) pairs,
       filtering out blank lines.
    2. Slide a window of BLOCK_SIZE over that list; hash each window.
    3. Record every hash → list[_BlockRef] in a global index.
    4. Any hash with >1 entry is a duplicate; emit a DuplicateIssue for
       every occurrence beyond the first.
    """
    # hash → list of (file_path, line_start, line_end) for all occurrences
    index: dict[str, list[_BlockRef]] = {}

    # (file_path_str → list of (line_start, line_end, block_hash))
    file_blocks: dict[str, list[tuple[int, int, str]]] = {}

    for path in files:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        content = _content_lines(source)

        if len(content) < BLOCK_SIZE:
            continue  # file too small for a full block

        path_str = str(path)
        file_blocks[path_str] = []

        for i in range(len(content) - BLOCK_SIZE + 1):
            window = content[i : i + BLOCK_SIZE]
            line_start = window[0][0]
            line_end   = window[-1][0]
            block_lines = [line for _, line in window]
            h = _hash_block(block_lines)

            index.setdefault(h, []).append((path_str, line_start, line_end))
            file_blocks[path_str].append((line_start, line_end, h))

    # Build per-file issue list
    results: dict[str, list[dict]] = {p: [] for p in file_blocks}

    for path_str, blocks in file_blocks.items():
        seen_ranges: set[tuple[int, int]] = set()  # avoid duplicate reports on same range

        for line_start, line_end, h in blocks:
            occurrences = index[h]
            if len(occurrences) < 2:
                continue  # unique block — no issue

            range_key = (line_start, line_end)
            if range_key in seen_ranges:
                continue
            seen_ranges.add(range_key)

            # Find the "other" occurrence (first one that is not this file+range)
            other = next(
                (ref for ref in occurrences if ref != (path_str, line_start, line_end)),
                None,
            )
            if other is None:
                continue

            other_path, other_start, other_end = other
            results[path_str].append({
                "line_start":   line_start,
                "line_end":     line_end,
                "duplicate_of": f"{other_path}:{other_start}-{other_end}",
            })

    return results
