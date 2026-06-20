"""
storage/collection.py — Qdrant collection-level operations
=============================================================
Everything that operates on a *collection* (create, reset, inspect, list
indexed papers) lives here. Connection setup lives in qdrant_client.py —
every function below takes an already-connected QdrantClient rather than
building its own. That's a deliberate Dependency Inversion fix: callers
control the connection lifecycle, and tests can pass in a mock client
instead of hitting a real Qdrant instance.
"""

from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PayloadSchemaType, VectorParams

from config import COLLECTION_NAME, EMBED_DIM

# Payload fields indexed for fast metadata filtering on every collection
_PAYLOAD_INDEXES = [
    ("source",  PayloadSchemaType.KEYWORD),
    ("section", PayloadSchemaType.KEYWORD),
    ("page",    PayloadSchemaType.INTEGER),
]


@dataclass
class CollectionStats:
    exists: bool
    points_count: int = 0


def get_collection_stats(
    client: QdrantClient,
    collection_name: str = COLLECTION_NAME,
) -> CollectionStats:
    """
    Return basic stats for a collection. Never raises — callers (e.g. the
    UI status sidebar, or the ingestion CLI's final summary) can call this
    without wrapping it in their own try/except, unlike the original code
    where this try/except was duplicated in three separate places.
    """
    try:
        info = client.get_collection(collection_name)
        return CollectionStats(exists=True, points_count=info.points_count)
    except Exception:
        return CollectionStats(exists=False)


def ensure_collection(
    client: QdrantClient,
    collection_name: str = COLLECTION_NAME,
    reset: bool = False,
) -> None:
    """
    Create the collection (with payload indexes) if it doesn't exist yet.
    If reset=True and the collection already exists, wipe it first.
    """
    exists = client.collection_exists(collection_name)

    if exists and reset:
        print(f"  ⚠  Resetting collection '{collection_name}'...")
        client.delete_collection(collection_name)
        exists = False

    if not exists:
        print(f"  ✦  Creating collection '{collection_name}' (dim={EMBED_DIM})...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
        )
        for field, schema in _PAYLOAD_INDEXES:
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field,
                field_schema=schema,
            )
        print("  ✦  Payload indexes created (source, section, page)")
    else:
        stats = get_collection_stats(client, collection_name)
        print(f"  ✦  Collection '{collection_name}' already exists "
              f"({stats.points_count} vectors) — appending new docs")


def list_papers(
    client: QdrantClient,
    collection_name: str = COLLECTION_NAME,
    page_size: int = 100,
) -> list[str]:
    """
    Return all unique source filenames currently indexed in the collection.
    Used by the UI to populate the paper dropdown.
    """
    filenames: set[str] = set()
    offset = None
    try:
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=page_size,
                with_payload=True,
                with_vectors=False,
                offset=offset,
            )
            for pt in points:
                fn = pt.payload.get("file_name") or pt.payload.get("source")
                if fn:
                    filenames.add(fn)
            if next_offset is None:
                break
            offset = next_offset
    except Exception:
        return []
    return sorted(filenames)
