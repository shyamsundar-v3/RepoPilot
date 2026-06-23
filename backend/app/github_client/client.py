import hashlib
import logging
import re
import shutil
import subprocess
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_github_url(url: str) -> str:
    pattern = r"^https://github\.com/[\w.\-]+/[\w.\-]+(?:\.git)?$"
    if not re.match(pattern, url):
        raise ValueError(f"Invalid GitHub URL: {url}")
    return url.rstrip("/").removesuffix(".git")


def repo_id_from_url(url: str) -> str:
    clean = validate_github_url(url)
    return hashlib.sha256(clean.encode()).hexdigest()[:12]


def clone_repo(url: str) -> tuple[str, Path]:
    clean = validate_github_url(url)
    repo_id = repo_id_from_url(url)
    dest = settings.repos_dir / repo_id

    # Only skip clone if the repo was actually cloned (has .git dir)
    if (dest / ".git").is_dir():
        logger.info("Repo %s already cloned at %s", repo_id, dest)
        return repo_id, dest

    # Clean up any leftover empty/broken directory from a prior failed clone
    if dest.exists():
        logger.warning("Cleaning up incomplete repo dir: %s", dest)
        shutil.rmtree(dest, ignore_errors=True)

    dest.mkdir(parents=True, exist_ok=True)

    cmd = ["git", "clone", "--depth", "1", clean, str(dest)]
    if settings.github_token:
        token_url = clean.replace("https://", f"https://x-access-token:{settings.github_token}@")
        cmd = ["git", "clone", "--depth", "1", token_url, str(dest)]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        logger.info("Successfully cloned %s -> %s", clean, dest)
    except subprocess.CalledProcessError as e:
        logger.error("git clone failed: %s\nstderr: %s", e, e.stderr)
        # Remove the broken directory so next attempt can retry
        shutil.rmtree(dest, ignore_errors=True)
        raise RuntimeError(f"git clone failed: {e.stderr}") from e

    return repo_id, dest


def get_repo_path(repo_id: str) -> Path:
    dest = settings.repos_dir / repo_id
    if not dest.exists():
        raise FileNotFoundError(f"Repo {repo_id} not cloned")
    return dest
