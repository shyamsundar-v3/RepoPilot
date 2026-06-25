import subprocess
from pathlib import Path

from app.github_client.client import get_repo_path


def search_code(repo_id: str, query: str, max_results: int = 20) -> list[dict]:
    root = get_repo_path(repo_id)
    try:
        result = subprocess.run(
            ["grep", "-rn", "--include=*", "-I", query, str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except FileNotFoundError:
        result = subprocess.run(
            ["findstr", "/s", "/n", "/p", query, str(root / "*")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            shell=True,
        )
    matches = []
    for line in result.stdout.splitlines()[:max_results]:
        parts = line.split(":", 2)
        if len(parts) >= 3:
            file_path = parts[0]
            try:
                rel = str(Path(file_path).relative_to(root))
            except ValueError:
                rel = file_path
            matches.append({
                "file": rel,
                "line": parts[1],
                "content": parts[2].strip(),
            })
    return matches


def find_references(repo_id: str, symbol: str, max_results: int = 20) -> list[dict]:
    return search_code(repo_id, symbol, max_results)
