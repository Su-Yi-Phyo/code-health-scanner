"""
main.py — FastAPI entry point for the Code Health Scanner.

POST /analyze
    Accepts a public GitHub repository URL, downloads the repository,
    scans for all supported source files (any language), runs the
    universal scoring agent (duplication + dead-code detection), and
    returns a structured JSON health report.

Response schema
---------------
{
    "repositoryUrl":   str,
    "fileCount":       int,
    "repositoryScore": float,          # 0 – 100  (higher = riskier)
    "folderScores":    { "<folder>": float, ... },
    "files": [
        {
            "file_path":  str,         # relative to repo root
            "language":   str,
            "line_count": int,
            "risk_score": float,       # 0 – 100  (higher = riskier / less optimized)
            "issues": {
                "duplicates": [ ... ],
                "dead_code":  [ ... ],
            }
        },
        ...
    ]
}
"""

import sys
import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the analysis package and scoring_agent package are importable
# when the server is launched from this directory.
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.github import download_repository, validate_github_url  # noqa: E402
from analysis.scanner import find_source_files, get_language           # noqa: E402
from scoring_agent.parser import parse_file                            # noqa: E402
from scoring_agent.detectors.duplication import detect_duplicates      # noqa: E402
from scoring_agent.detectors.dead_code import detect_dead_code         # noqa: E402
from scoring_agent.scorer import score_repository                      # noqa: E402

app = FastAPI(
    title="Code Health Scanner",
    description="Multi-language code health analyzer with duplication and dead-code detection.",
)

# Allow the frontend (any origin during development) to call the API.
# Restrict origins in production by replacing "*" with your domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class AnalyzeRequest(BaseModel):
    repositoryUrl: str


@app.get("/")
def root():
    return {"message": "Code Health Scanner is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Download a public GitHub repository and return a full code-health report.

    Steps
    -----
    1. Validate and download the repository to a temp directory.
    2. Discover all source files for all supported languages.
    3. Parse every file with tree-sitter (universal AST layer).
    4. Run duplication detector across all files.
    5. Run dead-code detector using the parse results.
    6. Score every file and aggregate to folder / repository level.
    7. Return the combined JSON report.
    8. Always clean up the temp directory.
    """

    # --- Validate URL -------------------------------------------------------
    try:
        validate_github_url(request.repositoryUrl)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    repository_path: str | None = None

    try:
        # --- Download -------------------------------------------------------
        repository_path = download_repository(request.repositoryUrl)
        repo_root = Path(repository_path)

        # --- Discover files -------------------------------------------------
        source_files = find_source_files(repository_path)

        # --- Parse (tree-sitter) -------------------------------------------
        parse_results: dict = {}
        for path in source_files:
            lang = get_language(path)
            pr = parse_file(path, lang)
            parse_results[str(path)] = pr

        # --- Detect issues --------------------------------------------------
        duplicates = detect_duplicates(source_files)
        dead_code  = detect_dead_code(source_files, parse_results)

        # --- Score ----------------------------------------------------------
        scoring_report = score_repository(
            files=source_files,
            parse_results=parse_results,
            duplicates=duplicates,
            dead_code=dead_code,
            repo_root=repo_root,
        )

        # --- Build response -------------------------------------------------
        files_list = [
            {"file_path": rel_path, **file_data}
            for rel_path, file_data in scoring_report["file_scores"].items()
        ]

        return {
            "repositoryUrl":   request.repositoryUrl,
            "fileCount":       len(files_list),
            "repositoryScore": scoring_report["repository_score"],
            "folderScores":    scoring_report["folder_scores"],
            "files":           files_list,
        }

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    finally:
        # Always clean up the temporary directory
        if repository_path is not None:
            parent = str(Path(repository_path).parent)
            shutil.rmtree(parent, ignore_errors=True)
