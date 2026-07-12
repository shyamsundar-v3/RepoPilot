"""Phase 2 verification: clone a test repo and exercise every tool."""
import sys
sys.path.insert(0, ".")

from app.github_client.client import clone_repo, repo_id_from_url
from app.mcp_server.server import call_tool

TEST_URL = "https://github.com/pallets/click"


def main():
    print("Cloning...")
    repo_id, path = clone_repo(TEST_URL)
    print(f"  repo_id={repo_id}  path={path}\n")

    print("list_files (first 10):")
    files = call_tool("list_files", repo_id=repo_id)
    for f in files[:10]:
        print(f"  {f}")
    print(f"  ... {len(files)} total\n")

    print("read_file (README.md):")
    content = call_tool("read_file", repo_id=repo_id, rel_path="README.md")
    print(f"  {len(content)} chars, first line: {content.splitlines()[0]}\n")

    print("search_code ('def '):")
    hits = call_tool("search_code", repo_id=repo_id, query="def ")
    for h in hits[:5]:
        print(f"  {h['file']}:{h['line']}  {h['content'][:80]}")
    print()

    print("get_git_history:")
    commits = call_tool("get_git_history", repo_id=repo_id)
    for c in commits[:3]:
        print(f"  {c['hash'][:8]} {c['author']} — {c['message']}")
    print()

    print("parse_dependencies:")
    deps = call_tool("parse_dependencies", repo_id=repo_id)
    for d in deps[:5]:
        print(f"  {d['name']}=={d['version']} ({d['source']})")
    print()

    print("All tools working.")


if __name__ == "__main__":
    main()
