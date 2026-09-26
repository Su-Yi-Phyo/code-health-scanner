"""
Phase 3 — Report Data Models

Defines every Pydantic schema that Phase 3 exposes to the UI.
These shapes are driven by Phase 2's actual output (scorer.py).

Phase 2 produces per file:
    {
        "file_path":  str,
        "language":   str,
        "line_count": int,
        "risk_score": float,          # 0–100
        "issues": {
            "duplicates": [ {line_start, line_end, duplicate_of}, ... ],
            "dead_code":  [ {name, kind, line_start, line_end},   ... ],
        }
    }
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskLabel = Literal["Healthy", "Watch", "Needs Attention", "High Risk"]


# ---------------------------------------------------------------------------
# Phase 2 issue sub-models
# ---------------------------------------------------------------------------

class DuplicateIssue(BaseModel):
    """One duplicate code block detected by Phase 2."""
    line_start: int
    line_end: int
    duplicate_of: str = Field(..., description="<other_file>:<start>-<end>")


class DeadCodeIssue(BaseModel):
    """One unused definition detected by Phase 2."""
    name: str
    kind: Literal["function", "class", "method"]
    line_start: int
    line_end: int


class FileIssues(BaseModel):
    duplicates: list[DuplicateIssue] = Field(default_factory=list)
    dead_code: list[DeadCodeIssue] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 2 input contract — exactly what /analyze returns per file
# ---------------------------------------------------------------------------

class FileMetrics(BaseModel):
    """
    Raw per-file data produced by Phase 2 (scorer.py → /analyze response).
    Phase 3 reads this and turns it into a FileReport.
    """
    path: str = Field(..., description="Relative path inside the repository")
    language: str = Field(default="unknown")
    line_count: int = Field(..., ge=0)
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Phase 2 raw score 0–100")
    issues: FileIssues = Field(default_factory=FileIssues)


# ---------------------------------------------------------------------------
# Phase 3 output — per-file report consumed by the UI
# ---------------------------------------------------------------------------

class FileReport(BaseModel):
    """
    Scored, annotated result for a single file.
    Feeds the file table and the file detail panel.
    """
    path: str
    language: str
    risk_score: int = Field(..., ge=0, le=100, description="Rounded 0–100 risk score")
    risk_label: RiskLabel
    line_count: int
    duplicate_block_count: int = Field(..., ge=0)
    dead_code_count: int = Field(..., ge=0)
    reasons: list[str] = Field(
        default_factory=list,
        description="Human-readable explanations shown in the file detail panel",
    )


# ---------------------------------------------------------------------------
# Scatter-chart point  (duplicate count vs lines)
# ---------------------------------------------------------------------------

class ScatterPoint(BaseModel):
    """One dot on the Issues vs Lines scatter chart."""
    path: str
    line_count: int
    duplicate_block_count: int
    dead_code_count: int
    risk_score: int
    risk_label: RiskLabel


# ---------------------------------------------------------------------------
# Top-N bar-chart entry
# ---------------------------------------------------------------------------

class TopRiskyFile(BaseModel):
    """One bar in the 'Top 10 riskiest files' bar chart."""
    rank: int = Field(..., ge=1)
    path: str
    language: str
    risk_score: int
    risk_label: RiskLabel


# ---------------------------------------------------------------------------
# Repository summary card
# ---------------------------------------------------------------------------

class RepositorySummary(BaseModel):
    """Aggregate numbers shown in the summary card."""
    repository: str = Field(..., description="owner/repo slug")
    file_count: int = Field(..., ge=0)
    total_lines: int = Field(..., ge=0)
    average_risk_score: float = Field(..., ge=0.0, le=100.0)
    high_risk_file_count: int = Field(..., ge=0)
    needs_attention_count: int = Field(..., ge=0)
    watch_count: int = Field(..., ge=0)
    healthy_count: int = Field(..., ge=0)
    total_duplicate_blocks: int = Field(..., ge=0)
    total_dead_code_items: int = Field(..., ge=0)


# ---------------------------------------------------------------------------
# Full report — single object returned by the API
# ---------------------------------------------------------------------------

class FullReport(BaseModel):
    """
    Top-level payload returned to the UI.

    The frontend derives every view from this one object:
      summary          → summary card
      top_risky_files  → bar chart (top 10)
      scatter_points   → issues vs lines scatter chart
      files            → sortable file table + detail panel
    """
    summary: RepositorySummary
    top_risky_files: list[TopRiskyFile] = Field(
        ..., description="Top 10 files by risk score, pre-sorted descending"
    )
    scatter_points: list[ScatterPoint] = Field(
        ..., description="All files as scatter-chart points"
    )
    files: list[FileReport] = Field(
        ..., description="All files sorted by risk score descending"
    )
