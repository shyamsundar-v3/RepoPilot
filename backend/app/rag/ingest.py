from pathlib import Path

from app.github_client.client import get_repo_path
from app.rag.vector_store import get_collection

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [c for c in chunks if c.strip()]


def ingest_repo(repo_id: str) -> int:
    root = get_repo_path(repo_id)
    collection = get_collection(repo_id)

    existing = collection.count()
    if existing > 0:
        return existing

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    idx = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue
        if path.suffix.lower() not in DOC_EXTENSIONS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(path.relative_to(root))
        chunks = _chunk_text(text)
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"file": rel, "chunk_index": i})
            ids.append(f"{repo_id}_{idx}")
            idx += 1

    if documents:
        batch = 100
        for i in range(0, len(documents), batch):
            collection.add(
                documents=documents[i : i + batch],
                metadatas=metadatas[i : i + batch],
                ids=ids[i : i + batch],
            )
    return len(documents)
