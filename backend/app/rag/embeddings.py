import os

# Disable ChromaDB telemetry before the chromadb package initializes
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY", "False")

import chromadb.utils.embedding_functions as ef

from app.core.config import settings


def get_embedding_function():
    return ef.DefaultEmbeddingFunction()
