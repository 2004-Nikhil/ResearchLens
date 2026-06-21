"""
ingestion/loader.py — load PDFs from disk into LlamaIndex Documents
=======================================================================
Owns exactly one responsibility: turning file paths into Document
objects, and organizing them by source file so the next stage
(chunker.py) can process one paper at a time. No chunking, no
embedding, and no Qdrant logic lives here.
"""

from pathlib import Path

from llama_index.core import SimpleDirectoryReader
from llama_index.core.schema import Document


def load_documents(pdf_paths: list[Path]) -> list[Document]:
    """Load one or more PDFs into LlamaIndex Document objects (one per page)."""
    print(f"\n📂  Loading {len(pdf_paths)} PDF(s)...")

    reader = SimpleDirectoryReader(
        input_files=[str(p) for p in pdf_paths],
        filename_as_id=True,
    )
    documents = reader.load_data()

    print(f"    Loaded {len(documents)} document page(s)")
    return documents


def group_by_source(documents: list[Document]) -> dict[str, list[Document]]:
    """
    Group document pages by their source filename so chunker.py can
    extract one abstract per paper and chunk each paper independently.
    """
    docs_by_file: dict[str, list[Document]] = {}
    for doc in documents:
        fname = doc.metadata.get("file_name", "unknown")
        docs_by_file.setdefault(fname, []).append(doc)
    return docs_by_file


def resolve_pdf_paths(papers_dir: Path, single_file: str | None = None) -> list[Path]:
    """
    Resolve which PDF(s) to load: a single file if `single_file` is given,
    otherwise every .pdf in `papers_dir`. Raises FileNotFoundError with a
    clear message on failure — the CLI decides how to print/exit on that,
    this function just answers "what should be loaded".
    """
    if single_file:
        path = Path(single_file)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {single_file}")
        return [path]

    if not papers_dir.exists():
        raise FileNotFoundError(f"{papers_dir}/ folder not found. Create it and drop PDFs in.")

    pdf_paths = sorted(papers_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found in {papers_dir}/. Drop some in and try again.")

    return pdf_paths
