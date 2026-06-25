"""
services/ingest_service.py — orchestrates the full ingestion pipeline
=========================================================================
Composes ingestion/ and storage/ into the actual pipeline: ensure
collection -> load -> group -> chunk -> embed/store. This is the one
place that pipeline exists.

Originally it was duplicated: ingest.py's main() and app.py's
run_upload() each independently called load_and_chunk() + build_clients()
+ embed_and_store() with slightly different surrounding code -- and
run_upload() skipped ensure_collection() entirely. That meant a fresh
Qdrant instance touched only through the Upload tab would get its
collection auto-created without the custom payload indexes (source,
section, page) that ensure_collection() sets up. Both the CLI and the
UI now call IngestService.ingest_papers(), so both paths always get the
same collection setup.
"""

from dataclasses import dataclass
from pathlib import Path

from llama_index.core import VectorStoreIndex

from config import COLLECTION_NAME
from ingestion.chunker import chunk_documents
from ingestion.embedder import embed_and_store
from ingestion.loader import group_by_source, load_documents, resolve_pdf_paths
from storage.collection import ensure_collection, get_collection_stats
from storage.qdrant_client import get_client_and_store


@dataclass
class IngestResult:
    indexed_files: list[Path]
    node_count: int
    points_count: int
    index: VectorStoreIndex


class IngestService:
    """
    Owns the ingestion pipeline. Stateless aside from which collection it
    targets -- no caching, no globals. Each call connects fresh, does the
    work, and returns a result; callers (CLI or UI) decide what to print
    or display.
    """

    def __init__(self, collection_name: str = COLLECTION_NAME):
        self.collection_name = collection_name

    def ingest_papers(self, pdf_paths: list[Path], reset: bool = False) -> IngestResult:
        """
        Run the full pipeline over the given PDF paths:
        ensure collection -> load -> group -> chunk -> embed/store.
        """
        client, store = get_client_and_store(self.collection_name)
        ensure_collection(client, self.collection_name, reset=reset)

        documents = load_documents(pdf_paths)
        docs_by_file = group_by_source(documents)
        nodes = chunk_documents(docs_by_file)

        index = embed_and_store(nodes, store)
        stats = get_collection_stats(client, self.collection_name)

        return IngestResult(
            indexed_files=pdf_paths,
            node_count=len(nodes),
            points_count=stats.points_count,
            index=index,
        )

    def ingest_from_papers_dir(
        self,
        papers_dir: Path,
        single_file: str | None = None,
        reset: bool = False,
    ) -> IngestResult:
        """Convenience wrapper: resolve paths from a folder (or single file) first."""
        pdf_paths = resolve_pdf_paths(papers_dir, single_file)
        return self.ingest_papers(pdf_paths, reset=reset)
