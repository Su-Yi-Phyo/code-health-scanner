"""
scorer.py — Universal code-health risk scorer.

Aggregates findings from the duplication and dead-code detectors into a
numeric RISK score (0 – 100) per file, then rolls up to folder-level and
repository-level averages.

Score meaning
-------------
    0   = perfectly clean, no issues detected
    100 = maximally risky / unoptimized

Scoring formula (per file)
--------------------------
    risk_score = (duplicate_block_count × DUPLICATE_WEIGHT)
               + (dead_code_count       × DEAD_CODE_WEIGHT)
    risk_score = min(100, risk_score)   # clamp to maximum 100

Folder / repository score
--------------------------
    folder_score     = mean of all file risk scores in that folder
    repository_score = mean of all file risk scores in the repository

Public API
----------
score_repository(files, parse_results, duplicates, dead_code, repo_root)
    -> ScoringReport  (plain dict, JSON-serialisable)

ScoringReport schema
--------------------
{
    "repository_score": float,          # 0 – 100  (higher = riskier)
    "folder_scores": {
        "<folder>": float,              # 0 – 100
        ...
    },
    "file_scores": {
        "<relative_file_path>": {
            "risk_score": float,        # 0 – 100  (higher = riskier)
            "language":   str,
            "line_count": int,
            "issues": {
                "duplicates": [ DuplicateIssue, ... ],
                "dead_code":  [ DeadCodeIssue,  ... ],
            }
        },
        ...
    }
}
"""

from __future__ import annotations

from pathlib import Path

from scoring_agent.parser import ParseResult


# ---------------------------------------------------------------------------
# Tunable weight constants
# ---------------------------------------------------------------------------

# Risk points added per duplicate block found in a file
DUPLICATE_WEIGHT: float = 5.0

# Risk points added per dead-code definition found in a file
DEAD_CODE_WEIGHT: float = 3.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _score_file(duplicate_issues: list[dict], dead_code_issues: list[dict]) -> float:
    """
    Compute the risk score for a single file.

    Starts at 0 (clean). Each issue adds weight. Capped at 100.
    Higher = riskier / less optimized.
    """
    risk = 0.0
    risk += len(duplicate_issues) * DUPLICATE_WEIGHT
    risk += len(dead_code_issues) * DEAD_CODE_WEIGHT
    return min(100.0, risk)


def _folder_key(relative_path: Path) -> str:
    """Return the parent folder string (or '.' for root-level files)."""
    parent = relative_path.parent
    return str(parent) if str(parent) != "." else "."


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_repository(
    files: list[Path],
    parse_results: dict[str, ParseResult],
    duplicates: dict[str, list[dict]],
    dead_code: dict[str, list[dict]],
    repo_root: str | Path,
) -> dict:
    """
    Produce a full ScoringReport for the repository.

    Parameters
    ----------
    files         : list of all source file Paths (absolute)
    parse_results : str(path) → ParseResult from parser.parse_file()
    duplicates    : str(path) → list of DuplicateIssue dicts
    dead_code     : str(path) → list of DeadCodeIssue dicts
    repo_root     : root path used to make file paths relative in output
    """
    root = Path(repo_root)

    file_scores: dict[str, dict] = {}
    folder_buckets: dict[str, list[float]] = {}
    all_scores: list[float] = []

    for path in files:
        path_str = str(path)

        # Relative path for output
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path

        rel_str = str(rel)

        # Gather issues for this file
        dup_issues = duplicates.get(path_str, [])
        dc_issues  = dead_code.get(path_str, [])

        file_risk = _score_file(dup_issues, dc_issues)
        all_scores.append(file_risk)

        # Language and line count from parse result
        pr = parse_results.get(path_str)
        language   = pr.language   if pr else "unknown"
        line_count = pr.source.count("\n") + 1 if (pr and pr.source) else 0

        file_scores[rel_str] = {
            "risk_score": round(file_risk, 2),
            "language":   language,
            "line_count": line_count,
            "issues": {
                "duplicates": dup_issues,
                "dead_code":  dc_issues,
            },
        }

        # Accumulate folder score
        folder = _folder_key(rel)
        folder_buckets.setdefault(folder, []).append(file_risk)

    # Roll-up folder scores
    folder_scores: dict[str, float] = {
        folder: round(_mean(scores), 2)
        for folder, scores in folder_buckets.items()
    }

    repository_score = round(_mean(all_scores), 2)

    return {
        "repository_score": repository_score,
        "folder_scores":    folder_scores,
        "file_scores":      file_scores,
    }
