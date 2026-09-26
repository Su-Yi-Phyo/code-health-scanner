"""
test_scoring_agent.py — Unit tests for the universal scoring agent.

Tests cover:
  1. Scanner: multi-language file discovery + get_language()
  2. Duplication detector: duplicate blocks flagged; unique files clean
  3. Dead-code detector: unused definitions flagged; used definitions clean
  4. Scorer: perfect file scores 100; penalised file deducts correctly;
             folder and repo averages are correct

No external network access or tree-sitter grammars are required for tests
1, 2, and 4 (they operate on raw text).  Test 3 uses tree-sitter and will
degrade gracefully if tree-sitter-languages is not installed.

Run from the backend/app directory:
    python scoring_agent/test_scoring_agent.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Make the app/ directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.scanner import (  # noqa: E402
    find_source_files,
    get_language,
    SUPPORTED_EXTENSIONS,
)
from scoring_agent.detectors.duplication import detect_duplicates   # noqa: E402
from scoring_agent.detectors.dead_code import detect_dead_code      # noqa: E402
from scoring_agent.scorer import score_repository, _score_file      # noqa: E402
from scoring_agent.parser import parse_file, ParseResult            # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


def tmp_file(suffix: str, content: str) -> Path:
    """Write *content* to a named temp file and return its Path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return Path(f.name)


# ---------------------------------------------------------------------------
# Test 1 — Scanner: multi-language discovery and get_language()
# ---------------------------------------------------------------------------

heading("Test 1 — Scanner: multi-language discovery & get_language()")

with tempfile.TemporaryDirectory() as tmp_dir:
    root = Path(tmp_dir)
    # Create files for several languages
    (root / "hello.py").write_text("print('hi')")
    (root / "main.js").write_text("console.log('hi')")
    (root / "App.java").write_text("class App {}")
    (root / "server.go").write_text("package main")
    (root / "README.md").write_text("# readme")    # not in SUPPORTED_EXTENSIONS
    (root / ".git").mkdir()
    (root / ".git" / "config").write_text("[core]")

    found = find_source_files(tmp_dir)
    paths = {p.name for p in found}

    check("hello.py"  in paths, "finds .py file")
    check("main.js"   in paths, "finds .js file")
    check("App.java"  in paths, "finds .java file")
    check("server.go" in paths, "finds .go file")
    check("README.md" not in paths, ".md not included (unsupported extension)")
    check("config"    not in paths, ".git directory contents excluded")
    check(len(found) == 4, f"total found files == 4 (got {len(found)})")

check(get_language(Path("foo.py"))   == "python",     "get_language .py returns python")
check(get_language(Path("foo.ts"))   == "typescript",  "get_language .ts returns typescript")
check(get_language(Path("foo.java")) == "java",        "get_language .java returns java")
check(get_language(Path("foo.xyz"))  == "unknown",     "get_language unknown ext returns unknown")

# ---------------------------------------------------------------------------
# Test 2 — Duplication detector
# ---------------------------------------------------------------------------

heading("Test 2 — Duplication Detector")

BLOCK = "\n".join([f"line_{i} = {i}" for i in range(10)])  # 10 non-blank lines

file_a = tmp_file(".py", BLOCK)
file_b = tmp_file(".py", BLOCK)          # identical → should be flagged
file_c = tmp_file(".py", "\n".join([f"unique_{i} = {i}" for i in range(10)]))  # unique

try:
    results = detect_duplicates([file_a, file_b, file_c])

    a_issues = results.get(str(file_a), [])
    b_issues = results.get(str(file_b), [])
    c_issues = results.get(str(file_c), [])

    check(len(a_issues) > 0,  "file_a (duplicate) has issues")
    check(len(b_issues) > 0,  "file_b (duplicate) has issues")
    check(len(c_issues) == 0, "file_c (unique) has no issues")

    if a_issues:
        issue = a_issues[0]
        check("line_start"   in issue, "issue has line_start")
        check("line_end"     in issue, "issue has line_end")
        check("duplicate_of" in issue, "issue has duplicate_of")
        check(issue["line_start"] >= 1, "line_start is 1-based")
finally:
    file_a.unlink(missing_ok=True)
    file_b.unlink(missing_ok=True)
    file_c.unlink(missing_ok=True)

# ---------------------------------------------------------------------------
# Test 3 — Dead-code detector
# ---------------------------------------------------------------------------

heading("Test 3 — Dead Code Detector (requires tree-sitter-languages)")

PY_WITH_DEAD = "def orphan_xyz():\n    pass\n\ndef used_func():\n    pass\n"
PY_CALLER    = "used_func()\n"  # references used_func but not orphan_xyz

f_dead   = tmp_file(".py", PY_WITH_DEAD)
f_caller = tmp_file(".py", PY_CALLER)

try:
    pr_dead   = parse_file(f_dead,   "python")
    pr_caller = parse_file(f_caller, "python")

    if pr_dead.parse_error or pr_caller.parse_error:
        print(f"  SKIP  tree-sitter unavailable: "
              f"{pr_dead.parse_error or pr_caller.parse_error}")
    else:
        parse_results = {
            str(f_dead):   pr_dead,
            str(f_caller): pr_caller,
        }
        dc_results = detect_dead_code([f_dead, f_caller], parse_results)

        dead_issues = dc_results.get(str(f_dead), [])
        names = {d["name"] for d in dead_issues}

        check("orphan_xyz" in names, "orphan_xyz flagged as dead code")
        check("used_func"  not in names, "used_func NOT flagged (it is called)")

        if dead_issues:
            issue = dead_issues[0]
            check("name"       in issue, "dead-code issue has 'name'")
            check("kind"       in issue, "dead-code issue has 'kind'")
            check("line_start" in issue, "dead-code issue has 'line_start'")
            check("line_end"   in issue, "dead-code issue has 'line_end'")
finally:
    f_dead.unlink(missing_ok=True)
    f_caller.unlink(missing_ok=True)

# ---------------------------------------------------------------------------
# Test 4 — Scorer
# ---------------------------------------------------------------------------

heading("Test 4 — Scorer  (0=clean, 100=max risk)")

# 4a: file with no issues -> risk_score = 0
score_clean = _score_file([], [])
check(score_clean == 0.0, f"clean file risk is 0 (got {score_clean})")

# 4b: file with 2 duplicate blocks and 1 dead-code item
#     expected = 2*5 + 1*3 = 13
score_risky = _score_file(
    [{"line_start": 1, "line_end": 6, "duplicate_of": "other.py:1-6"},
     {"line_start": 10, "line_end": 15, "duplicate_of": "other.py:10-15"}],
    [{"name": "dead_fn", "kind": "function", "line_start": 20, "line_end": 25}],
)
check(score_risky == 13.0, f"risky file scores 13 (got {score_risky})")

# 4c: risk_score cannot exceed 100
score_cap = _score_file(
    [{"duplicate_of": "x"} for _ in range(30)],
    [{"name": f"fn{i}"} for i in range(30)],
)
check(score_cap == 100.0, f"risk capped at 100 (got {score_cap})")

# 4d: score_repository produces correct structure
with tempfile.TemporaryDirectory() as tmp_dir:
    root = Path(tmp_dir)
    fa = root / "a.py"
    fb = root / "b.js"
    fa.write_text("x = 1\n")
    fb.write_text("var x = 1;\n")

    pr_a = ParseResult(language="python",     source="x = 1\n")
    pr_b = ParseResult(language="javascript", source="var x = 1;\n")

    report = score_repository(
        files=[fa, fb],
        parse_results={str(fa): pr_a, str(fb): pr_b},
        duplicates={},
        dead_code={},
        repo_root=root,
    )

    check("repository_score" in report,  "report has repository_score")
    check("folder_scores"    in report,  "report has folder_scores")
    check("file_scores"      in report,  "report has file_scores")
    check(report["repository_score"] == 0.0, "all-clean repo has risk 0")
    check(len(report["file_scores"]) == 2,   "file_scores has 2 entries")

    first_file = next(iter(report["file_scores"].values()))
    check("risk_score" in first_file, "file entry has risk_score")
    check("language"   in first_file, "file entry has language")
    check("line_count" in first_file, "file entry has line_count")
    check("issues"     in first_file, "file entry has issues")
    check("duplicates" in first_file["issues"], "issues has duplicates")
    check("dead_code"  in first_file["issues"], "issues has dead_code")

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
