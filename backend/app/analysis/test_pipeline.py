"""
test_pipeline.py – Integration tests for the POST /analyze endpoint.

Uses FastAPI's TestClient (backed by httpx) so the full request/response
cycle is exercised without a running server.

Two test scenarios:
  1. Valid repository URL  →  200 with correct response shape
  2. Invalid URL           →  422 with an error detail message

The live-network test downloads a small real GitHub repository
(octocat/Hello-World) so it requires internet access.  It is kept minimal
and only verifies response structure, not exact file content, so it stays
stable regardless of future repository changes.
"""

import sys
from pathlib import Path

# Allow running from the analysis directory directly
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402

client = TestClient(app)

PASS = "  PASS"
FAIL = "  FAIL"
failures: list[str] = []


def heading(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def check(condition: bool, message: str) -> None:
    if condition:
        print(f"{PASS}  {message}")
    else:
        print(f"{FAIL}  {message}")
        failures.append(message)


# ---------------------------------------------------------------------------
# Test 1 – Invalid URL returns 422
# ---------------------------------------------------------------------------

heading("Test 1 – Invalid GitHub URL returns 422")

response = client.post("/analyze", json={"repositoryUrl": "https://not-github.com/owner/repo"})

print(f"  Status code: {response.status_code}")
print(f"  Body: {response.json()}")

check(response.status_code == 422, "status code is 422")
check("detail" in response.json(), "response has 'detail' key")

# ---------------------------------------------------------------------------
# Test 2 – Missing repositoryUrl field returns 422 (Pydantic validation)
# ---------------------------------------------------------------------------

heading("Test 2 – Missing required field returns 422")

response = client.post("/analyze", json={})

print(f"  Status code: {response.status_code}")
print(f"  Body: {response.json()}")

check(response.status_code == 422, "status code is 422 for missing field")

# ---------------------------------------------------------------------------
# Test 3 – Valid public repository returns correct structure (live network)
# ---------------------------------------------------------------------------

heading("Test 3 – Valid repository returns structured JSON (live network)")

REPO_URL = "https://github.com/psf/requests"

print(f"  Sending POST /analyze for {REPO_URL} ...")

try:
    response = client.post("/analyze", json={"repositoryUrl": REPO_URL}, timeout=120)
    print(f"  Status code: {response.status_code}")

    check(response.status_code == 200, "status code is 200")

    body = response.json()

    # Top-level keys
    check("repositoryUrl" in body, "response has 'repositoryUrl'")
    check("fileCount" in body, "response has 'fileCount'")
    check("files" in body, "response has 'files'")

    check(body["repositoryUrl"] == REPO_URL, "repositoryUrl echoed back correctly")
    check(isinstance(body["fileCount"], int), "fileCount is an integer")
    check(isinstance(body["files"], list), "files is a list")
    check(body["fileCount"] == len(body["files"]), "fileCount matches files list length")

    # If there are any Python files, check the per-file structure
    if body["files"]:
        first = body["files"][0]
        print(f"\n  First file sample: {first['file_path']!r}")
        for key in ("file_path", "line_count", "syntax_error", "imports", "functions", "classes"):
            check(key in first, f"file result has '{key}' key")
        check(isinstance(first["line_count"], int), "line_count is an integer")
        check(isinstance(first["imports"], list), "imports is a list")
        check(isinstance(first["functions"], list), "functions is a list")
        check(isinstance(first["classes"], list), "classes is a list")
    else:
        print("  (repository has no Python files — skipping per-file checks)")

except Exception as exc:
    print(f"  ERROR: {exc}")
    failures.append(f"Test 3 raised an exception: {exc}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

heading("Summary")

if failures:
    print(f"\n  {len(failures)} FAILURE(S):")
    for f in failures:
        print(f"    - {f}")
    sys.exit(1)
else:
    print("\n  All checks passed!")
    sys.exit(0)
