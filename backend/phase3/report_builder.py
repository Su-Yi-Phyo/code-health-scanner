"""
Phase 3 — Report Builder

Converts Phase 2's raw per-file output (FileMetrics) into a FullReport
ready to be serialised and returned to the UI.

Phase 2 scoring formula (scorer.py):
    risk_score = (duplicate_blocks × 5) + (dead_code_items × 3), clamped to 100

Phase 3 adds:
  - risk_label  (Healthy / Watch / Needs Attention / High Risk)
  - reasons[]   (human-readable explanation of the score)
  - Aggregate summary card
  - Pre-sorted top-10 bar chart list
  - Scatter-chart points (issues vs lines)
"""

from __future__ import annotations

from backend.phase3.models import (
    FileMetrics,
    FileReport,
    FullReport,
    RepositorySummary,
    RiskLabel,
    ScatterPoint,
    TopRiskyFile,
)


# ---------------------------------------------------------------------------
# Risk label thresholds  (0–29 Healthy, 30–49 Watch, 50–69 Needs Attention, 70–100 High Risk)
# ---------------------------------------------------------------------------

def _risk_label(score: int) -> RiskLabel:
    if score < 30:
        return "Healthy"
    if score < 50:
        return "Watch"
    if score < 70:
        return "Needs Attention"
    return "High Risk"


# ---------------------------------------------------------------------------
# Reason generation — driven by Phase 2's actual issue lists
# ---------------------------------------------------------------------------

def _build_reasons(metrics: FileMetrics) -> list[str]:
    reasons: list[str] = []
    dup_count = len(metrics.issues.duplicates)
    dc_count  = len(metrics.issues.dead_code)

    # Duplicate blocks
    if dup_count >= 2:
        reasons.append(f"{dup_count} duplicate code blocks detected")
    elif dup_count == 1:
        block = metrics.issues.duplicates[0]
        reasons.append(
            f"Duplicate code block at lines {block.line_start}–{block.line_end} "
            f"(duplicates {block.duplicate_of})"
        )

    # Dead code definitions
    if dc_count >= 3:
        names = ", ".join(f"`{d.name}`" for d in metrics.issues.dead_code[:3])
        suffix = f" and {dc_count - 3} more" if dc_count > 3 else ""
        reasons.append(f"Unused definitions: {names}{suffix}")
    elif dc_count == 2:
        names = " and ".join(f"`{d.name}`" for d in metrics.issues.dead_code)
        reasons.append(f"Unused definitions: {names}")
    elif dc_count == 1:
        d = metrics.issues.dead_code[0]
        reasons.append(
            f"Unused {d.kind} `{d.name}` "
            f"(lines {d.line_start}–{d.line_end})"
        )

    # File size note (informational, not a scoring input)
    if metrics.line_count >= 400:
        reasons.append(f"Large file: {metrics.line_count} lines")
    elif metrics.line_count >= 200:
        reasons.append(f"Medium-sized file: {metrics.line_count} lines")

    if not reasons:
        reasons.append("No significant issues detected")

    return reasons


# ---------------------------------------------------------------------------
# Per-file conversion
# ---------------------------------------------------------------------------

def _make_file_report(metrics: FileMetrics) -> FileReport:
    score = max(0, min(100, int(metrics.risk_score)))
    return FileReport(
        path=metrics.path,
        language=metrics.language,
        risk_score=score,
        risk_label=_risk_label(score),
        line_count=metrics.line_count,
        duplicate_block_count=len(metrics.issues.duplicates),
        dead_code_count=len(metrics.issues.dead_code),
        reasons=_build_reasons(metrics),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_report(repo_slug: str, file_metrics: list[FileMetrics]) -> FullReport:
    """
    Transform Phase 2 FileMetrics into a FullReport for the UI.

    Args:
        repo_slug:    Repository identifier in "owner/repo" format.
        file_metrics: Per-file output from Phase 2's score_repository().

    Returns:
        FullReport with summary, top_risky_files, scatter_points, and files.
    """
    if not file_metrics:
        return FullReport(
            summary=RepositorySummary(
                repository=repo_slug,
                file_count=0,
                total_lines=0,
                average_risk_score=0.0,
                high_risk_file_count=0,
                needs_attention_count=0,
                watch_count=0,
                healthy_count=0,
                total_duplicate_blocks=0,
                total_dead_code_items=0,
            ),
            top_risky_files=[],
            scatter_points=[],
            files=[],
        )

    # Convert and sort
    scored = [_make_file_report(m) for m in file_metrics]
    scored.sort(key=lambda f: f.risk_score, reverse=True)

    # Aggregates
    total_lines      = sum(m.line_count for m in file_metrics)
    avg_risk         = sum(f.risk_score for f in scored) / len(scored)
    total_dups       = sum(f.duplicate_block_count for f in scored)
    total_dead       = sum(f.dead_code_count for f in scored)
    high_risk_count  = sum(1 for f in scored if f.risk_label == "High Risk")
    needs_att_count  = sum(1 for f in scored if f.risk_label == "Needs Attention")
    watch_count      = sum(1 for f in scored if f.risk_label == "Watch")
    healthy_count    = sum(1 for f in scored if f.risk_label == "Healthy")

    summary = RepositorySummary(
        repository=repo_slug,
        file_count=len(scored),
        total_lines=total_lines,
        average_risk_score=round(avg_risk, 1),
        high_risk_file_count=high_risk_count,
        needs_attention_count=needs_att_count,
        watch_count=watch_count,
        healthy_count=healthy_count,
        total_duplicate_blocks=total_dups,
        total_dead_code_items=total_dead,
    )

    # Top 10 bar chart
    top_risky = [
        TopRiskyFile(
            rank=i + 1,
            path=f.path,
            language=f.language,
            risk_score=f.risk_score,
            risk_label=f.risk_label,
        )
        for i, f in enumerate(scored[:10])
    ]

    # Scatter chart — all files
    scatter = [
        ScatterPoint(
            path=f.path,
            line_count=f.line_count,
            duplicate_block_count=f.duplicate_block_count,
            dead_code_count=f.dead_code_count,
            risk_score=f.risk_score,
            risk_label=f.risk_label,
        )
        for f in scored
    ]

    return FullReport(
        summary=summary,
        top_risky_files=top_risky,
        scatter_points=scatter,
        files=scored,
    )
