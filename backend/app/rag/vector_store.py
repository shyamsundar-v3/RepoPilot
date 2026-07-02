import threading

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

from app.core.config import settings
from app.rag.embeddings import get_embedding_function

# Report sections now run concurrently (see orchestration/workflow.py), and
# both the "docs" and "dev_guide" sections hit this at essentially the same
# time via docs_agent -> retrieve(). Serialize client/collection creation so
# two threads never race to instantiate a PersistentClient on the same path.
_lock = threading.Lock()


def get_client() -> chromadb.ClientAPI:
    persist_dir = str(settings.chroma_dir)
    with _lock:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        return chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )


def get_collection(repo_id: str):
    client = get_client()
    ef = get_embedding_function()
    with _lock:
        return client.get_or_create_collection(
            name=f"repo_{repo_id}",
            embedding_function=ef,
        )
