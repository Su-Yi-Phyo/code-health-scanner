"""
Phase 3 — FastAPI Router

Endpoints
---------
GET  /report/mock          → FullReport built from built-in mock data (dev / demo)
GET  /report/summary/mock  → RepositorySummary only (mock)
GET  /report/files/mock    → Sorted FileReport list only (mock)
POST /report               → FullReport from real Phase 2 /analyze output

Phase 2 calls POST /report with the body it already returns from /analyze:
    {
        "repositoryUrl": "https://github.com/owner/repo",
        "fileCount": 42,
        "repositoryScore": 38.5,
        "folderScores": { ... },
        "files": [
            {
                "file_path":  "src/payment.py",
                "language":   "python",
                "line_count": 612,
                "risk_score": 85.0,
                "issues": {
                    "duplicates": [...],
                    "dead_code":  [...]
                }
            },
            ...
        ]
    }
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.phase3.mock_data import MOCK_REPO_SLUG, get_mock_file_metrics
from backend.phase3.models import FileMetrics, FileReport, FullReport, RepositorySummary
from backend.phase3.report_builder import build_report

router = APIRouter(prefix="/report", tags=["Phase 3 — Report"])


# ---------------------------------------------------------------------------
# Request model — matches the Phase 2 /analyze response exactly
# ---------------------------------------------------------------------------

class Phase2FileEntry(BaseModel):
    """One file entry as returned by Phase 2's score_repository()."""
    file_path: str                      # Phase 2 uses file_path, not path
    language: str = "unknown"
    line_count: int = Field(..., ge=0)
    risk_score: float = Field(..., ge=0.0, le=100.0)
    issues: dict = Field(default_factory=lambda: {"duplicates": [], "dead_code": []})


class Phase2ReportRequest(BaseModel):
    """
    Mirrors the full body that Phase 2 POST /analyze returns.
    Phase 3 only needs repositoryUrl and files[]; other fields are passed through.
    """
    repositoryUrl: str
    fileCount: int = 0
    repositoryScore: float = 0.0
    folderScores: dict = Field(default_factory=dict)
    files: list[Phase2FileEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helper — normalise Phase 2 file entry → FileMetrics
# ---------------------------------------------------------------------------

def _to_file_metrics(entry: Phase2FileEntry) -> FileMetrics:
    """
    Convert a Phase 2 file entry to the FileMetrics model Phase 3 expects.
    The only difference is field name: Phase 2 uses `file_path`, Phase 3 uses `path`.
    """
    return FileMetrics(
        path=entry.file_path,
        language=entry.language,
        line_count=entry.line_count,
        risk_score=entry.risk_score,
        issues=entry.issues,  # Pydantic coerces the dict to FileIssues
    )


def _repo_slug_from_url(url: str) -> str:
    """Extract 'owner/repo' from a github.com URL. Falls back to the raw URL."""
    url = url.rstrip("/")
    if "github.com/" in url:
        return "/".join(url.split("github.com/", 1)[1].split("/")[:2])
    return url


# ---------------------------------------------------------------------------
# Mock endpoints  (no Phase 2 needed)
# ---------------------------------------------------------------------------

@router.get(
    "/mock",
    response_model=FullReport,
    summary="Full report — mock data",
    description="Returns a complete FullReport from built-in mock data. "
                "Use this to build and test the frontend without running Phase 2.",
)
def get_mock_report() -> FullReport:
    return build_report(MOCK_REPO_SLUG, get_mock_file_metrics())


@router.get(
    "/summary/mock",
    response_model=RepositorySummary,
    summary="Repository summary card — mock data",
)
def get_mock_summary() -> RepositorySummary:
    return build_report(MOCK_REPO_SLUG, get_mock_file_metrics()).summary


@router.get(
    "/files/mock",
    response_model=list[FileReport],
    summary="Sorted file list — mock data",
    description="All files sorted by risk score descending. Feeds the sortable file table.",
)
def get_mock_files() -> list[FileReport]:
    return build_report(MOCK_REPO_SLUG, get_mock_file_metrics()).files


# ---------------------------------------------------------------------------
# Real endpoint — called by Phase 2 after /analyze completes
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=FullReport,
    summary="Full report from Phase 2 output",
    description=(
        "Accepts the JSON body that Phase 2's POST /analyze already returns. "
        "Adds risk labels, human-readable reasons, and pre-built chart datasets."
    ),
)
def post_report(payload: Phase2ReportRequest) -> FullReport:
    file_metrics = [_to_file_metrics(f) for f in payload.files]
    repo_slug = _repo_slug_from_url(payload.repositoryUrl)
    return build_report(repo_slug, file_metrics)
