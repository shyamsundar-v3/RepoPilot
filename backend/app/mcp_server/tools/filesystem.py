from pathlib import Path

from app.github_client.client import get_repo_path


def _safe_resolve(repo_id: str, rel_path: str) -> Path:
    root = get_repo_path(repo_id).resolve()
    target = (root / rel_path).resolve()
    if not str(target).startswith(str(root)):
        raise PermissionError(f"Path traversal blocked: {rel_path}")
    return target


def list_files(repo_id: str, subdir: str = ".") -> list[str]:
    root = get_repo_path(repo_id).resolve()
    target = _safe_resolve(repo_id, subdir)
    results = []
    for p in sorted(target.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            # Use .as_posix() to always return forward slashes, even on Windows.
            # LLMs naturally cite paths with forward slashes, so this prevents
            # false "FILE NOT FOUND" mismatches in the reviewer.
            results.append(p.relative_to(root).as_posix())
    return results


def read_file(repo_id: str, rel_path: str) -> str:
    target = _safe_resolve(repo_id, rel_path)
    if not target.is_file():
        raise FileNotFoundError(f"Not a file: {rel_path}")
    return target.read_text(encoding="utf-8", errors="replace")
