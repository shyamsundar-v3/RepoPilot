import json
from pathlib import Path

from app.github_client.client import get_repo_path


def parse_dependencies(repo_id: str) -> list[dict]:
    root = get_repo_path(repo_id)
    deps: list[dict] = []

    pkg_json = root / "package.json"
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
        for name, ver in data.get("dependencies", {}).items():
            deps.append({"name": name, "version": ver, "source": "package.json", "type": "runtime"})
        for name, ver in data.get("devDependencies", {}).items():
            deps.append({"name": name, "version": ver, "source": "package.json", "type": "dev"})

    req_txt = root / "requirements.txt"
    if req_txt.exists():
        for line in req_txt.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("==")
                name = parts[0].strip()
                ver = parts[1].strip() if len(parts) > 1 else "*"
                deps.append({"name": name, "version": ver, "source": "requirements.txt", "type": "runtime"})

    go_mod = root / "go.mod"
    if go_mod.exists():
        in_require = False
        for line in go_mod.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("require"):
                in_require = True
                continue
            if in_require and line == ")":
                in_require = False
                continue
            if in_require and line:
                parts = line.split()
                if len(parts) >= 2:
                    deps.append({"name": parts[0], "version": parts[1], "source": "go.mod", "type": "runtime"})

    return deps
