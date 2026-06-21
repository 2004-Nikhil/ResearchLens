"""
ingestion/chunker.py — abstract extraction + body chunking
===============================================================
Owns exactly one responsibility: turning loaded Document pages into
TextNodes ready for embedding — one abstract node per paper (when an
abstract can be found) plus body chunks via SentenceSplitter. Loading
PDFs is loader.py's job; embedding/storing is embedder.py's job.
"""

import re

from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document, TextNode
from tqdm import tqdm

from config import CHUNK_OVERLAP, CHUNK_SIZE


def extract_abstract(text: str) -> str | None:
    """
    Try to extract the abstract from raw PDF text using multiple strategies.
    Handles arXiv, IEEE, ACM, and general academic paper formats.
    Returns the abstract string, or None if not found.

    NOTE: ported verbatim from the original ingest.py, including the
    regex patterns as originally written. Worth a second look later —
    the doubled braces in strategies 1 and 3 (e.g. {{2,}}) parse as
    "2+ literal brace characters" rather than "2+ repetitions", since
    this is a plain raw string, not an f-string. Not changing it here
    since the ask was to preserve core logic, but flagging since it
    likely makes strategy 3 effectively unreachable on real PDF text.
    """
    # Search a wider window -- some PDFs have long title/author blocks
    window = text[:5000]

    strategies = [
        # Strategy 1: "Abstract—" with em-dash (IEEE/conference format)
        re.compile(
            r"Abstract\s*[\u2014\u2013\-]\s*(.*?)(?:\n{{2,}}|\bKeywords\b|\bIndex Terms\b|\bIntroduction\b)",
            re.IGNORECASE | re.DOTALL,
        ),
        # Strategy 2: "Abstract" as header, content on next line(s)
        re.compile(
            r"(?:^|\n)[ \t]*Abstract[ \t]*[:\-]?[ \t]*\n(.*?)(?:\n\s*\n|\n\s*(?:\d+\.?\s+)?Introduction)",
            re.IGNORECASE | re.DOTALL,
        ),
        # Strategy 3: ALL-CAPS ABSTRACT (some IEEE/ACM formats)
        re.compile(
            r"ABSTRACT[\s\u2014\u2013\-:]*([A-Z][^\n]{{20,}}.*?)(?:\n{{2,}}|I\.\s+INTRODUCTION)",
            re.DOTALL,
        ),
        # Strategy 4: loose fallback
        re.compile(
            r"abstract\s*[\u2014\u2013:\-]?\s*(.{100,1200}?)\s*(?:keywords|index terms|introduction|1\.)",
            re.IGNORECASE | re.DOTALL,
        ),
    ]

    for pattern in strategies:
        match = pattern.search(window)
        if match:
            abstract = match.group(1).strip()
            # Sanity: must be at least 80 chars and contain real words
            if len(abstract) >= 80 and abstract.count(" ") > 10:
                return abstract

    return None


def build_abstract_node(doc: Document, abstract_text: str) -> TextNode:
    """
    Create a dedicated TextNode for the abstract, tagged with section='abstract'.
    This improves summarization quality — the abstract won't get mixed into
    methodology or conclusion chunks during retrieval.
    """
    return TextNode(
        text=abstract_text,
        metadata={
            "source":  doc.metadata.get("file_name", "unknown"),
            "section": "abstract",
            "page":    1,
        },
        excluded_embed_metadata_keys=["section", "page"],
        excluded_llm_metadata_keys=["page"],
    )


def _chunk_paper(fname: str, pages: list[Document], splitter: SentenceSplitter) -> list[TextNode]:
    """Chunk a single paper's pages into an abstract node (if found) + body nodes."""
    nodes: list[TextNode] = []

    # ── Abstract node (first page text only) ──
    first_page_text = pages[0].text if pages else ""
    abstract = extract_abstract(first_page_text)
    if abstract:
        nodes.append(build_abstract_node(pages[0], abstract))

    # ── Body nodes ────────────────────────────
    body_nodes = splitter.get_nodes_from_documents(pages)
    for node in body_nodes:
        # Enrich each node with clean, consistent metadata
        node.metadata["source"]  = fname
        node.metadata["section"] = "body"
        node.metadata["page"]    = int(node.metadata.get("page_label", 0) or 0)
        node.excluded_embed_metadata_keys = ["section", "page"]
        node.excluded_llm_metadata_keys   = ["page"]
    nodes.extend(body_nodes)

    return nodes


def chunk_documents(docs_by_file: dict[str, list[Document]]) -> list[TextNode]:
    """
    Chunk every paper in `docs_by_file` (as produced by loader.group_by_source)
    into abstract + body TextNodes ready for embedding.
    """
    splitter = SentenceSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    all_nodes: list[TextNode] = []

    print(f"\n✂   Chunking {len(docs_by_file)} paper(s)...")
    for fname, pages in tqdm(docs_by_file.items(), desc="Papers"):
        all_nodes.extend(_chunk_paper(fname, pages, splitter))

    n_abstract = sum(1 for n in all_nodes if n.metadata.get("section") == "abstract")
    n_body     = sum(1 for n in all_nodes if n.metadata.get("section") == "body")
    print(f"    Total nodes: {len(all_nodes)} ({n_abstract} abstract(s), {n_body} body chunk(s))")

    return all_nodes
