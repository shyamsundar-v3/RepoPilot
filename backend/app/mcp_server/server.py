import inspect

from app.mcp_server.tools import filesystem, search, git, dependencies

TOOLS = {
    "list_files": {
        "fn": filesystem.list_files,
        "description": "List all files in the repo or a subdirectory",
        "params": {"repo_id": "str", "subdir": "str (optional)"},
    },
    "read_file": {
        "fn": filesystem.read_file,
        "description": "Read a file from the repo",
        "params": {"repo_id": "str", "rel_path": "str"},
    },
    "search_code": {
        "fn": search.search_code,
        "description": "Search for a string/pattern in repo code",
        "params": {"repo_id": "str", "query": "str"},
    },
    "find_references": {
        "fn": search.find_references,
        "description": "Find references to a symbol",
        "params": {"repo_id": "str", "symbol": "str"},
    },
    "get_git_history": {
        "fn": git.get_git_history,
        "description": "Get recent commit history",
        "params": {"repo_id": "str"},
    },
    "get_commit": {
        "fn": git.get_commit,
        "description": "Show a specific commit",
        "params": {"repo_id": "str", "commit_id": "str"},
    },
    "get_diff": {
        "fn": git.get_diff,
        "description": "Show diff for a commit",
        "params": {"repo_id": "str", "commit_id": "str"},
    },
    "parse_dependencies": {
        "fn": dependencies.parse_dependencies,
        "description": "Parse project dependencies",
        "params": {"repo_id": "str"},
    },
}


def get_tool(name: str):
    entry = TOOLS.get(name)
    if not entry:
        raise KeyError(f"Unknown tool: {name}")
    return entry["fn"]


def list_tools() -> list[dict]:
    return [
        {"name": k, "description": v["description"], "params": v["params"]}
        for k, v in TOOLS.items()
    ]


def call_tool(name: str, **kwargs):
    fn = get_tool(name)
    # Models (esp. Gemini) sometimes attach extra "explanation" fields like
    # `reason` that aren't real parameters. Drop anything the function doesn't
    # actually accept instead of letting it crash the whole tool call.
    accepted = set(inspect.signature(fn).parameters)
    clean_kwargs = {k: v for k, v in kwargs.items() if k in accepted}
    return fn(**clean_kwargs)
