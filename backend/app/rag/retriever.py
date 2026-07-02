from app.rag.vector_store import get_collection


def retrieve(repo_id: str, query: str, top_k: int = 5) -> list[dict]:
    collection = get_collection(repo_id)
    if collection.count() == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
    items = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i] if results["metadatas"] else {}
        dist = results["distances"][0][i] if results.get("distances") else None
        items.append({
            "text": doc,
            "file": meta.get("file", ""),
            "chunk_index": meta.get("chunk_index", 0),
            "distance": dist,
        })
    return items
