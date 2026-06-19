"""
storage/qdrant_client.py — Qdrant connection management
==========================================================
Owns exactly one responsibility: handing back a connected QdrantClient
(and, optionally, a QdrantVectorStore wrapping it). No collection logic,
no ingestion logic, no query logic lives here — see collection.py for
collection-level operations (create, reset, list papers, stats).
"""

from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME


def get_qdrant_client() -> QdrantClient:
    """
    Return a new connected QdrantClient.

    check_compatibility=False avoids a noisy version-mismatch error when the
    qdrant-client package and the Qdrant server are on slightly different
    versions (common in Docker/Codespaces setups). Originally only query.py
    passed this flag — standardized here so every caller behaves the same.
    """
    return QdrantClient(
        host=QDRANT_HOST,
        port=QDRANT_PORT,
        check_compatibility=False,
    )


def get_vector_store(
    client: QdrantClient,
    collection_name: str = COLLECTION_NAME,
) -> QdrantVectorStore:
    """Wrap a QdrantClient in a LlamaIndex-compatible QdrantVectorStore."""
    return QdrantVectorStore(client=client, collection_name=collection_name)


def get_client_and_store(
    collection_name: str = COLLECTION_NAME,
) -> tuple[QdrantClient, QdrantVectorStore]:
    """Convenience: build both the client and its vector store in one call."""
    client = get_qdrant_client()
    store = get_vector_store(client, collection_name)
    return client, store
