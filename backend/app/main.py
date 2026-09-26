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

import os
import sys
import shutil
from pathlib import Path
from typing import List

# Load .env from project root (repo_root/backend/app/../../.. = repo_root).
# python-dotenv is a no-op when the file doesn't exist, so this is safe in
# production where the platform injects secrets as real environment variables.
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure the analysis package and scoring_agent package are importable
# when the server is launched from this directory.
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.github import download_repository, validate_github_url, fetch_raw_file  # noqa: E402
from analysis.scanner import find_source_files, get_language                           # noqa: E402
from scoring_agent.parser import parse_file                                            # noqa: E402
from scoring_agent.detectors.duplication import detect_duplicates                      # noqa: E402
from scoring_agent.detectors.dead_code import detect_dead_code                         # noqa: E402
from scoring_agent.scorer import score_repository                                      # noqa: E402
from ai_agent.explainer import explain_issues                                          # noqa: E402

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


# HF token — read once at startup; endpoint degrades gracefully when absent.
HF_API_TOKEN: str = os.environ.get("HF_API_TOKEN", "")


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    repositoryUrl: str


class ExplainRequest(BaseModel):
    repositoryUrl: str
    file_path: str


class ExplainResponse(BaseModel):
    file_path: str
    explanation: str
    suggestions: List[str]
    model_used: str = ""


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


@app.post("/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    """
    Fetch a single file from a GitHub repository and return an AI-generated
    explanation of its code quality issues plus concrete refactoring suggestions.

    The caller supplies only the repository URL and file path — both are already
    present in the response from POST /analyze.  The backend re-fetches the file
    content directly from GitHub's raw content API (no full repo download).

    Steps
    -----
    1. Fetch the file source text from GitHub raw content API.
    2. Derive the language from the file extension.
    3. Call the Granite explanation agent with the source text.
    4. Return the explanation and suggestions.
    """
    # --- Fetch file source from GitHub --------------------------------------
    try:
        source_code = fetch_raw_file(request.repositoryUrl, request.file_path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch file: {exc}")

    # --- Derive language from file extension --------------------------------
    language = get_language(Path(request.file_path)) or "unknown"

    # --- Call AI explanation agent ------------------------------------------
    result = explain_issues(
        file_path=request.file_path,
        language=language,
        source_code=source_code,
        duplicates=[],
        dead_code=[],
        hf_token=HF_API_TOKEN,
    )

    return ExplainResponse(
        file_path=request.file_path,
        explanation=result["explanation"],
        suggestions=result["suggestions"],
        model_used=result.get("model_used", ""),
    )
