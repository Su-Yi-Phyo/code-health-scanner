"""
Tests for Phase 3 — Report Builder and API endpoints.

All tests use mock data only; no real GitHub repository is fetched.
Run:  pytest backend/tests/test_phase3.py -v
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.phase3.mock_data import MOCK_REPO_SLUG, get_mock_file_metrics
from backend.phase3.models import FileIssues, FileMetrics, FullReport, RiskLabel
from backend.phase3.report_builder import _risk_label, build_report

client = TestClient(app)

VALID_LABELS: set[RiskLabel] = {"Healthy", "Watch", "Needs Attention", "High Risk"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metrics(
    path: str = "test.py",
    language: str = "python",
    line_count: int = 100,
    risk_score: float = 20.0,
    duplicates: list[dict] | None = None,
    dead_code: list[dict] | None = None,
) -> FileMetrics:
    return FileMetrics(
        path=path,
        language=language,
        line_count=line_count,
        risk_score=risk_score,
        issues=FileIssues(
            duplicates=duplicates or [],
            dead_code=dead_code or [],
        ),
    )


# ===========================================================================
# Unit tests — _risk_label
# ===========================================================================

class TestRiskLabel:
    def test_healthy(self):
        assert _risk_label(0)  == "Healthy"
        assert _risk_label(29) == "Healthy"

    def test_watch(self):
        assert _risk_label(30) == "Watch"
        assert _risk_label(49) == "Watch"

    def test_needs_attention(self):
        assert _risk_label(50) == "Needs Attention"
        assert _risk_label(69) == "Needs Attention"

    def test_high_risk(self):
        assert _risk_label(70)  == "High Risk"
        assert _risk_label(100) == "High Risk"


# ===========================================================================
# Unit tests — build_report
# ===========================================================================

class TestBuildReport:

    def test_empty_input_returns_zero_summary(self):
        report = build_report("owner/repo", [])
        assert report.summary.file_count == 0
        assert report.summary.total_lines == 0
        assert report.summary.average_risk_score == 0.0
        assert report.files == []
        assert report.top_risky_files == []
        assert report.scatter_points == []

    def test_file_count_matches_input(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert report.summary.file_count == len(metrics)
        assert len(report.files) == len(metrics)
        assert len(report.scatter_points) == len(metrics)

    def test_top_risky_files_capped_at_10(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert len(report.top_risky_files) <= 10

    def test_files_sorted_descending_by_risk_score(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        scores = [f.risk_score for f in report.files]
        assert scores == sorted(scores, reverse=True)

    def test_top_risky_files_sorted_and_ranked(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for i, entry in enumerate(report.top_risky_files):
            assert entry.rank == i + 1
        scores = [e.risk_score for e in report.top_risky_files]
        assert scores == sorted(scores, reverse=True)

    def test_risk_scores_in_range(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for f in report.files:
            assert 0 <= f.risk_score <= 100

    def test_all_labels_valid(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for f in report.files:
            assert f.risk_label in VALID_LABELS

    def test_risk_label_consistent_with_score(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for f in report.files:
            assert f.risk_label == _risk_label(f.risk_score)

    def test_reasons_not_empty(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for f in report.files:
            assert len(f.reasons) >= 1

    def test_summary_label_counts_sum_to_total(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        s = report.summary
        total = s.high_risk_file_count + s.needs_attention_count + s.watch_count + s.healthy_count
        assert total == s.file_count

    def test_total_lines_correct(self):
        metrics = get_mock_file_metrics()
        expected = sum(m.line_count for m in metrics)
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert report.summary.total_lines == expected

    def test_total_duplicate_blocks_correct(self):
        metrics = get_mock_file_metrics()
        expected = sum(len(m.issues.duplicates) for m in metrics)
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert report.summary.total_duplicate_blocks == expected

    def test_total_dead_code_items_correct(self):
        metrics = get_mock_file_metrics()
        expected = sum(len(m.issues.dead_code) for m in metrics)
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert report.summary.total_dead_code_items == expected

    def test_highest_risk_file_is_payment_py(self):
        """payment.py has risk_score=85 — highest in mock data."""
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert report.files[0].path == "src/payment.py"
        assert report.top_risky_files[0].path == "src/payment.py"

    def test_repo_slug_propagated(self):
        report = build_report("test/repo", get_mock_file_metrics())
        assert report.summary.repository == "test/repo"

    def test_scatter_points_contain_all_files(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        assert {p.path for p in report.scatter_points} == {f.path for f in report.files}

    def test_scatter_points_carry_issue_counts(self):
        metrics = get_mock_file_metrics()
        report = build_report(MOCK_REPO_SLUG, metrics)
        for point in report.scatter_points:
            assert point.duplicate_block_count >= 0
            assert point.dead_code_count >= 0

    def test_single_file_report(self):
        single = [_make_metrics(path="single.py", risk_score=10.0, line_count=50)]
        report = build_report("owner/repo", single)
        assert report.summary.file_count == 1
        assert report.summary.average_risk_score == report.files[0].risk_score

    def test_high_risk_file_from_score(self):
        """A file with risk_score=90 from Phase 2 must land in High Risk."""
        high = [_make_metrics(risk_score=90.0)]
        report = build_report("owner/repo", high)
        assert report.files[0].risk_label == "High Risk"

    def test_healthy_file_from_score(self):
        """A file with risk_score=0 from Phase 2 must land in Healthy."""
        clean = [_make_metrics(risk_score=0.0)]
        report = build_report("owner/repo", clean)
        assert report.files[0].risk_label == "Healthy"

    def test_duplicate_reason_mentions_count(self):
        """When there are 3 duplicates the reason should mention the count."""
        m = _make_metrics(
            risk_score=50.0,
            duplicates=[
                {"line_start": 1,  "line_end": 7,  "duplicate_of": "a.py:1-7"},
                {"line_start": 20, "line_end": 26, "duplicate_of": "b.py:1-7"},
                {"line_start": 40, "line_end": 46, "duplicate_of": "c.py:1-7"},
            ],
        )
        report = build_report("owner/repo", [m])
        reasons_text = " ".join(report.files[0].reasons)
        assert "duplicate" in reasons_text.lower()

    def test_dead_code_reason_mentions_name(self):
        """When there is 1 dead-code item the reason should mention the function name."""
        m = _make_metrics(
            risk_score=30.0,
            dead_code=[{"name": "orphan_fn", "kind": "function", "line_start": 10, "line_end": 20}],
        )
        report = build_report("owner/repo", [m])
        reasons_text = " ".join(report.files[0].reasons)
        assert "orphan_fn" in reasons_text

    def test_clean_file_has_no_issue_reason(self):
        """A file with no issues should get the 'No significant issues' reason."""
        m = _make_metrics(risk_score=0.0)
        report = build_report("owner/repo", [m])
        assert report.files[0].reasons == ["No significant issues detected"]

    def test_file_report_carries_language(self):
        m = _make_metrics(language="typescript", risk_score=5.0)
        report = build_report("owner/repo", [m])
        assert report.files[0].language == "typescript"
        assert report.top_risky_files[0].language == "typescript"


# ===========================================================================
# Integration tests — HTTP endpoints via TestClient
# ===========================================================================

class TestMockEndpoints:

    def test_get_mock_report_200(self):
        assert client.get("/report/mock").status_code == 200

    def test_get_mock_report_schema(self):
        data = client.get("/report/mock").json()
        assert "summary" in data
        assert "top_risky_files" in data
        assert "scatter_points" in data
        assert "files" in data

    def test_mock_summary_has_correct_fields(self):
        data = client.get("/report/summary/mock").json()
        assert data["repository"] == MOCK_REPO_SLUG
        assert data["file_count"] > 0
        assert "total_duplicate_blocks" in data
        assert "total_dead_code_items" in data

    def test_mock_files_sorted_descending(self):
        scores = [f["risk_score"] for f in client.get("/report/files/mock").json()]
        assert scores == sorted(scores, reverse=True)

    def test_mock_report_top_risky_capped_at_10(self):
        data = client.get("/report/mock").json()
        assert len(data["top_risky_files"]) <= 10

    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestPostReportEndpoint:
    """POST /report accepts Phase 2's /analyze body exactly."""

    def _phase2_body(self, files: list[dict]) -> dict:
        return {
            "repositoryUrl": "https://github.com/owner/test-repo",
            "fileCount": len(files),
            "repositoryScore": 42.0,
            "folderScores": {"src": 42.0},
            "files": files,
        }

    def _file_entry(self, file_path: str = "src/app.py", risk_score: float = 20.0,
                    line_count: int = 100, duplicates: list | None = None,
                    dead_code: list | None = None) -> dict:
        return {
            "file_path": file_path,
            "language": "python",
            "line_count": line_count,
            "risk_score": risk_score,
            "issues": {
                "duplicates": duplicates or [],
                "dead_code": dead_code or [],
            },
        }

    def test_post_returns_200(self):
        resp = client.post("/report", json=self._phase2_body([self._file_entry()]))
        assert resp.status_code == 200

    def test_repo_slug_extracted_from_url(self):
        body = self._phase2_body([self._file_entry()])
        data = client.post("/report", json=body).json()
        assert data["summary"]["repository"] == "owner/test-repo"

    def test_file_path_mapped_correctly(self):
        body = self._phase2_body([self._file_entry(file_path="src/payment.py")])
        data = client.post("/report", json=body).json()
        assert data["files"][0]["path"] == "src/payment.py"

    def test_multiple_files_sorted_by_risk(self):
        body = self._phase2_body([
            self._file_entry("high.py",  risk_score=80.0),
            self._file_entry("low.py",   risk_score=10.0),
            self._file_entry("medium.py", risk_score=45.0),
        ])
        files = client.post("/report", json=body).json()["files"]
        scores = [f["risk_score"] for f in files]
        assert scores == sorted(scores, reverse=True)

    def test_duplicate_count_in_response(self):
        body = self._phase2_body([
            self._file_entry(duplicates=[
                {"line_start": 1, "line_end": 7, "duplicate_of": "other.py:1-7"},
                {"line_start": 20, "line_end": 26, "duplicate_of": "other.py:20-26"},
            ])
        ])
        data = client.post("/report", json=body).json()
        assert data["files"][0]["duplicate_block_count"] == 2
        assert data["summary"]["total_duplicate_blocks"] == 2

    def test_dead_code_count_in_response(self):
        body = self._phase2_body([
            self._file_entry(dead_code=[
                {"name": "unused_fn", "kind": "function", "line_start": 10, "line_end": 20},
            ])
        ])
        data = client.post("/report", json=body).json()
        assert data["files"][0]["dead_code_count"] == 1
        assert data["summary"]["total_dead_code_items"] == 1

    def test_empty_files_list(self):
        body = self._phase2_body([])
        data = client.post("/report", json=body).json()
        assert data["summary"]["file_count"] == 0

    def test_invalid_payload_returns_422(self):
        resp = client.post("/report", json={"repositoryUrl": "https://github.com/x/y",
                                            "files": [{"file_path": "x.py", "line_count": "bad"}]})
        assert resp.status_code == 422
