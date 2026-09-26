"""
Phase 3 — Mock Data

Mimics the exact JSON that Phase 2's POST /analyze returns under the "files" key.
Each entry matches the FileMetrics schema (path, language, line_count, risk_score, issues).

Usage:
    from backend.phase3.mock_data import MOCK_REPO_SLUG, get_mock_file_metrics
"""

from __future__ import annotations

from backend.phase3.models import DeadCodeIssue, DuplicateIssue, FileIssues, FileMetrics

MOCK_REPO_SLUG = "octocat/python-demo-repo"

# ---------------------------------------------------------------------------
# Raw dicts — mirror what scorer.py actually serialises
# ---------------------------------------------------------------------------
_RAW: list[dict] = [
    {
        "path": "src/payment.py",
        "language": "python",
        "line_count": 612,
        "risk_score": 85.0,
        "issues": {
            "duplicates": [
                {"line_start": 45,  "line_end": 51,  "duplicate_of": "src/billing.py:120-126"},
                {"line_start": 198, "line_end": 204, "duplicate_of": "src/refund.py:88-94"},
                {"line_start": 310, "line_end": 316, "duplicate_of": "src/billing.py:200-206"},
            ],
            "dead_code": [
                {"name": "_legacy_calculate", "kind": "function", "line_start": 88,  "line_end": 112},
                {"name": "_old_validator",    "kind": "function", "line_start": 300, "line_end": 318},
                {"name": "DeprecatedPaymentHelper", "kind": "class", "line_start": 410, "line_end": 480},
            ],
        },
    },
    {
        "path": "src/parser.py",
        "language": "python",
        "line_count": 420,
        "risk_score": 65.0,
        "issues": {
            "duplicates": [
                {"line_start": 78,  "line_end": 84,  "duplicate_of": "src/lexer.py:45-51"},
                {"line_start": 200, "line_end": 206, "duplicate_of": "src/tokenizer.py:90-96"},
            ],
            "dead_code": [
                {"name": "_unused_token_handler", "kind": "function", "line_start": 150, "line_end": 165},
                {"name": "_debug_dump",           "kind": "function", "line_start": 380, "line_end": 395},
            ],
        },
    },
    {
        "path": "src/auth.py",
        "language": "python",
        "line_count": 390,
        "risk_score": 60.0,
        "issues": {
            "duplicates": [
                {"line_start": 55, "line_end": 61, "duplicate_of": "src/session.py:30-36"},
                {"line_start": 90, "line_end": 96, "duplicate_of": "src/middleware.py:10-16"},
            ],
            "dead_code": [
                {"name": "_old_hash_password", "kind": "function", "line_start": 200, "line_end": 220},
            ],
        },
    },
    {
        "path": "src/database.py",
        "language": "python",
        "line_count": 310,
        "risk_score": 50.0,
        "issues": {
            "duplicates": [
                {"line_start": 100, "line_end": 106, "duplicate_of": "src/cache.py:40-46"},
            ],
            "dead_code": [
                {"name": "_migrate_v1", "kind": "function", "line_start": 260, "line_end": 290},
                {"name": "LegacyConnection", "kind": "class", "line_start": 295, "line_end": 309},
            ],
        },
    },
    {
        "path": "src/api/routes.py",
        "language": "python",
        "line_count": 275,
        "risk_score": 40.0,
        "issues": {
            "duplicates": [
                {"line_start": 60, "line_end": 66, "duplicate_of": "src/api/admin_routes.py:20-26"},
            ],
            "dead_code": [
                {"name": "_deprecated_endpoint", "kind": "function", "line_start": 240, "line_end": 260},
            ],
        },
    },
    {
        "path": "src/api/middleware.py",
        "language": "python",
        "line_count": 190,
        "risk_score": 30.0,
        "issues": {
            "duplicates": [
                {"line_start": 30, "line_end": 36, "duplicate_of": "src/auth.py:90-96"},
            ],
            "dead_code": [],
        },
    },
    {
        "path": "src/utils/helpers.py",
        "language": "python",
        "line_count": 155,
        "risk_score": 25.0,
        "issues": {
            "duplicates": [],
            "dead_code": [
                {"name": "_unused_format", "kind": "function", "line_start": 120, "line_end": 130},
            ],
        },
    },
    {
        "path": "src/utils/validators.py",
        "language": "python",
        "line_count": 120,
        "risk_score": 15.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/models/user.py",
        "language": "python",
        "line_count": 95,
        "risk_score": 10.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/models/product.py",
        "language": "python",
        "line_count": 88,
        "risk_score": 5.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/config.py",
        "language": "python",
        "line_count": 72,
        "risk_score": 5.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/models/order.py",
        "language": "python",
        "line_count": 65,
        "risk_score": 3.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/constants.py",
        "language": "python",
        "line_count": 40,
        "risk_score": 0.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/exceptions.py",
        "language": "python",
        "line_count": 35,
        "risk_score": 0.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
    {
        "path": "src/schemas.py",
        "language": "python",
        "line_count": 28,
        "risk_score": 0.0,
        "issues": {
            "duplicates": [],
            "dead_code": [],
        },
    },
]


def get_mock_file_metrics() -> list[FileMetrics]:
    """Return mock Phase 2 output as validated FileMetrics objects."""
    return [FileMetrics(**row) for row in _RAW]
