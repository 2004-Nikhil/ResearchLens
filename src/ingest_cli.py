"""
ingest_cli.py — command-line entry point for the ingestion pipeline
=======================================================================
Thin CLI: parse args, print the human-readable banner, hand off to
IngestService for the actual work, print the final summary. No
LlamaIndex/Qdrant logic lives here — see services/ingest_service.py
and the ingestion/ package for that.

Usage:
    python src/ingest_cli.py                  # index all PDFs in papers/
    python src/ingest_cli.py --reset          # wipe collection first, then re-index
    python src/ingest_cli.py --file foo.pdf   # index a single file

Renamed from the original ingest.py to match query_cli.py. This one
didn't strictly need it for collision reasons (the "ingestion" package
and "ingest_cli.py" never shared a name either way) — it's renamed
purely so the CLI layer is consistent and easy to spot at a glance.
"""

import argparse
import sys

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    EMBED_MODEL,
    PAPERS_DIR,
    QDRANT_HOST,
    QDRANT_PORT,
)
from ingestion.loader import resolve_pdf_paths
from services.ingest_service import IngestService


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDFs into Qdrant")
    parser.add_argument("--reset", action="store_true",
                         help="Wipe the Qdrant collection before indexing")
    parser.add_argument("--file", type=str, default=None,
                         help="Index a single PDF file instead of the whole papers/ folder")
    args = parser.parse_args()

    try:
        pdf_paths = resolve_pdf_paths(PAPERS_DIR, args.file)
    except FileNotFoundError as e:
        print(f"❌  {e}")
        sys.exit(1)

    print(f"\n{'='*52}")
    print("  Research Paper Summarizer — Ingestion Pipeline")
    print(f"{'='*52}")
    print(f"  Papers dir : {PAPERS_DIR.resolve()}")
    print(f"  PDFs found : {len(pdf_paths)}")
    print(f"  Qdrant     : {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"  Collection : {COLLECTION_NAME}")
    print(f"  Embed model: {EMBED_MODEL}")
    print(f"  Chunk size : {CHUNK_SIZE} tokens (+{CHUNK_OVERLAP} overlap)")
    print(f"{'='*52}\n")

    for p in pdf_paths:
        print(f"  📄  {p.name}")
    print()

    service = IngestService(collection_name=COLLECTION_NAME)
    result = service.ingest_papers(pdf_paths, reset=args.reset)

    print(f"\n{'='*52}")
    print("  ✅  Ingestion complete!")
    print(f"  Vectors in Qdrant : {result.points_count}")
    print(f"  Papers indexed    : {len(result.indexed_files)}")
    print("\n  Next step → python src/app.py")
    print(f"{'='*52}\n")


if __name__ == "__main__":
    main()