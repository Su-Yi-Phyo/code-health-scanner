from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import json
import tempfile
import zipfile


def validate_github_url(repository_url: str) -> tuple[str, str]:
    """Validate a public GitHub repository URL and return owner, repo."""

    parsed = urlparse(repository_url)

    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise ValueError("Only public github.com URLs are allowed.")

    parts = parsed.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("Invalid GitHub repository URL.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")

    return owner, repo


def get_default_branch(owner: str, repo: str) -> str:
    """Get the repository's default branch from GitHub."""

    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    request = Request(
        api_url,
        headers={"User-Agent": "Python-Code-Health-Scanner"}
    )

    with urlopen(request, timeout=20) as response:
        data = json.load(response)

    return data["default_branch"]


def download_repository(repository_url: str) -> str:
    """
    Download a public GitHub repository into a temporary directory.

    Returns:
        Path to the extracted repository.
    """

    owner, repo = validate_github_url(repository_url)

    branch = get_default_branch(owner, repo)

    zip_url = (
        f"https://github.com/{owner}/{repo}"
        f"/archive/refs/heads/{branch}.zip"
    )

    temp_dir = Path(tempfile.mkdtemp(prefix="code_health_"))
    zip_path = temp_dir / "repository.zip"

    request = Request(
        zip_url,
        headers={"User-Agent": "Python-Code-Health-Scanner"}
    )

    with urlopen(request, timeout=60) as response:
        zip_path.write_bytes(response.read())

    extract_dir = temp_dir / "source"
    extract_dir.mkdir()

    with zipfile.ZipFile(zip_path, "r") as zip_file:
        zip_file.extractall(extract_dir)

    zip_path.unlink()

    return str(extract_dir)