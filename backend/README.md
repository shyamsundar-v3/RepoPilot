# RepoPilot

Local-only repository analysis tool.

## Setup

RepoPilot uses [OmniRoute](https://www.npmjs.com/package/omniroute) as its
LLM gateway — start it first, in its own terminal:

```bash
npm install -g omniroute
omniroute
```

Then set up the backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Defaults already point at OmniRoute on localhost:20128/v1 — only edit
# .env if you changed OmniRoute's port, want to pin a specific model, or
# need GITHUB_TOKEN to clone private repos.
uvicorn app.main:app --reload --port 8000
```

⚠️ Use `python run.py` for local dev instead of the raw `uvicorn --reload`
command above when you can. `--reload`'s default watcher covers the whole
`backend/` directory, including `app/data/` where cloned repos land — the
instant `git clone` writes a `.py` file there, WatchFiles treats it as a
source change and restarts the whole server mid-analysis, silently
orphaning the in-progress job and hanging the frontend forever waiting for
a "done" event that will never arrive. `run.py` sets up the same reload
behavior but excludes `app/data/` from the watch set.
