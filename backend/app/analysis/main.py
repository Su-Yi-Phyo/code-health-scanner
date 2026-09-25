import shutil
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from github import download_repository, validate_github_url
from scanner import find_python_files
from ast_analyzer import analyze_file

app = FastAPI(
    title="Python Code Health Scanner",
    description="Phase 1 - Python code structure analyzer"
)


class AnalyzeRequest(BaseModel):
    repositoryUrl: str


@app.get("/")
def root():
    return {
        "message": "Python Code Health Scanner is running"
    }


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    """
    Download a public GitHub repository, find all Python source files,
    analyze each one with the AST analyzer, and return structured results.
    """

    # Validate the URL before downloading anything
    try:
        validate_github_url(request.repositoryUrl)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    repository_path: str | None = None

    try:
        repository_path = download_repository(request.repositoryUrl)

        python_files = find_python_files(repository_path)

        analyzed_files = [analyze_file(path) for path in python_files]

        # Make file_path relative to the repository root for cleaner output
        root = Path(repository_path)
        for result in analyzed_files:
            try:
                result["file_path"] = str(
                    Path(result["file_path"]).relative_to(root)
                )
            except ValueError:
                pass  # keep absolute path if relative conversion fails

        return {
            "repositoryUrl": request.repositoryUrl,
            "fileCount": len(analyzed_files),
            "files": analyzed_files,
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
