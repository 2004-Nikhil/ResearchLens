"""
query/runner.py — execute search and summarize queries
==========================================================
Owns exactly one responsibility: running a query against an already-built
index and streaming back (token, sources, elapsed, is_done) tuples.
Building the index/engine is engine.py's job; this module just uses them.

NOTE on a deliberate signature change from the original query.py:
search() and summarize() now take `index` as their first argument
instead of silently building and caching one via module-level globals
(`_settings_initialised`, `_index`). That hidden singleton was this
project's one piece of global mutable state — it's not gone, just moved
to where it belongs: services/query_service.py will own one explicit,
named instance and pass it in here, rather than every function reaching
into shared module state behind the scenes.

format_result(), warmup(), and start_keepalive() from the original
query.py are intentionally NOT here: format_result() is terminal output
formatting (a CLI concern, will live in query_cli.py), and warmup() /
start_keepalive() manage the LLM's process lifecycle (a service concern,
will live in services/query_service.py alongside the index singleton).
"""

import json
import time

from llama_index.core import VectorStoreIndex

from query.engine import build_search_engine, build_summarize_engine
from query.models import SourceNode


def _extract_text(node) -> str:
    """
    Safely extract text from a node -- LlamaIndex stores it either in
    node.text or inside the _node_content JSON payload.
    """
    text = getattr(node, "text", None) or getattr(node, "get_text", lambda: "")()
    if not text:
        # Fallback: parse from raw payload
        nc = node.metadata.get("_node_content", "{}")
        try:
            text = json.loads(nc).get("text", "") if isinstance(nc, str) else ""
        except (json.JSONDecodeError, AttributeError):
            text = ""
    return text.strip()


def _nodes_to_sources(response) -> list[SourceNode]:
    """Convert LlamaIndex response source nodes into clean SourceNode objects."""
    sources = []
    seen = set()
    for node_with_score in (response.source_nodes or []):
        node  = node_with_score.node
        score = round(node_with_score.score or 0.0, 4)
        fname = node.metadata.get("file_name") or node.metadata.get("source", "unknown")
        sec   = node.metadata.get("section", "body")
        page  = int(node.metadata.get("page", 0) or 0)
        text  = _extract_text(node)[:150].replace("\n", " ")

        # Deduplicate by (file, page) -- same page can appear in multiple chunks
        key = (fname, page)
        if key not in seen:
            seen.add(key)
            sources.append(SourceNode(
                filename=fname,
                section=sec,
                page=page,
                score=score,
                preview=text,
            ))
    return sources


def search(index: VectorStoreIndex, query: str):
    """
    Streaming semantic search across ALL indexed papers.
    Yields (token, sources, elapsed, is_done) tuples so the UI can
    display tokens as they arrive rather than waiting for the full response.
    """
    t0 = time.time()
    try:
        engine = build_search_engine(index)
        streaming_response = engine.query(query)

        for token in streaming_response.response_gen:
            yield token, [], round(time.time() - t0, 1), False

        sources = _nodes_to_sources(streaming_response)
        yield "", sources, round(time.time() - t0, 1), True

    except Exception as e:
        yield f"**Error:** {e}", [], round(time.time() - t0, 1), True


def summarize(index: VectorStoreIndex, filename: str, query: str = "Summarize this paper."):
    """
    Streaming summarization of a SINGLE paper filtered by filename.
    Yields (token, sources, elapsed, is_done) tuples.
    """
    t0 = time.time()
    try:
        engine = build_summarize_engine(index, filename)
        streaming_response = engine.query(query)

        for token in streaming_response.response_gen:
            yield token, [], round(time.time() - t0, 1), False

        sources = _nodes_to_sources(streaming_response)
        yield "", sources, round(time.time() - t0, 1), True

    except Exception as e:
        yield f"**Error:** {e}", [], round(time.time() - t0, 1), True
