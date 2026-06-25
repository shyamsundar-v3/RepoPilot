import subprocess
from pathlib import Path

from app.github_client.client import get_repo_path


def _run_git(repo_id: str, args: list[str]) -> str:
    root = get_repo_path(repo_id)
    result = subprocess.run(
        ["git", "-C", str(root)] + args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git error: {result.stderr.strip()}")
    return result.stdout


def get_git_history(repo_id: str, max_commits: int = 50) -> list[dict]:
    raw = _run_git(repo_id, [
        "log",
        f"--max-count={max_commits}",
        "--pretty=format:%H||%an||%ad||%s",
        "--date=iso",
    ])
    commits = []
    for line in raw.strip().splitlines():
        parts = line.split("||", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "date": parts[2],
                "message": parts[3],
            })
    return commits


def get_commit(repo_id: str, commit_id: str) -> str:
    return _run_git(repo_id, ["show", "--stat", commit_id])


def get_diff(repo_id: str, commit_id: str) -> str:
    return _run_git(repo_id, ["show", commit_id])
