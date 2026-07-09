"""
Dev server entrypoint.

Why this exists instead of `uvicorn app.main:app --reload`:

`--reload` (WatchFiles) by default watches the *entire* current working
directory. RepoPilot clones analyzed repos into app/data/repos/<id>/ and
writes the RAG index into app/data/chroma/ — both inside that watched tree.
The instant `git clone` or ChromaDB writes a file there, WatchFiles treats
it as a source change and restarts the whole server process.

That restart wipes job_manager and trace_bus (plain in-memory dicts), so
any analysis running in the background thread pool is orphaned: its
websocket gets force-closed, the frontend reconnects, and the new server
process has never heard of that job_id. The UI then waits forever for a
"done" event that will never come.

Fix: only watch the actual source directories, and explicitly exclude
app/data/** so cloning/indexing a repo never triggers a restart.

Implementation note: uvicorn's reload_excludes only recurses into
subdirectories when the entry is a real, *existing*, *absolute* directory
path — passed as a relative path or glob (e.g. "app/data/*") it only
matches one or two path segments and misses deeply-nested cloned repo
trees. We resolve settings.data_dir (creating it if needed) and hand
uvicorn its absolute path instead.
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    settings.data_dir.mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["app"],
        reload_excludes=[str(settings.data_dir.resolve())],
    )
