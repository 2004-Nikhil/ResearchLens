"""
ui/builder.py — assemble the Gradio app from its tabs + theme
==================================================================
The only place that knows the overall page layout: header, tabs,
sidebar. Each tab's components/logic live in ui/tabs/ — this module
just composes them and wires the one cross-tab dependency (Upload
needs to refresh Summarize's paper dropdown).

NOTE: THEME/CSS from ui/theme.py are NOT applied here. Verified against
gradio==6.19.0: gr.Blocks() no longer accepts theme/css (moved to
.launch() in Gradio 6.0). The future app.py entry point should call:

    from ui.theme import THEME, CSS
    app.launch(theme=THEME, css=CSS, server_name=..., server_port=...)

`title` is unaffected and still belongs on the Blocks() constructor.
"""

import gradio as gr
import httpx

from config import CHUNK_OVERLAP, CHUNK_SIZE, EMBED_MODEL, LLM_MODEL, OLLAMA_HOST
from services.ingest_service import IngestService
from services.query_service import QueryService
from storage.collection import get_collection_stats
from storage.qdrant_client import get_qdrant_client
from ui.tabs.search import build_search_tab
from ui.tabs.summarize import build_summarize_tab
from ui.tabs.upload import build_upload_tab

HEADER_HTML = (
    '<div class="app-eyebrow">Local · Offline · Your Library</div>'
    '<h1 class="app-title">Research Library</h1>'
    '<p class="app-subtitle">A RAG reading desk for your papers — '
    f'LlamaIndex · Qdrant · Ollama · <code>{LLM_MODEL}</code>. '
    "Nothing leaves this Codespace.</p>"
)

HOW_TO_USE = (
    "### How to use\n"
    "1. Drop PDFs into `papers/` and run `python src/ingest.py`, "
    "or use the **Upload** tab\n"
    "2. **Search** for cross-paper questions\n"
    "3. **Summarize** for deep single-paper analysis\n"
)


def _get_system_status_html() -> str:
    """
    Render the sidebar's live Qdrant/Ollama status. Deliberate, scoped
    exception to "UI only talks to services/": this is a read-only
    infrastructure health check with no business logic in it, so it
    talks to storage/ directly rather than through QueryService.

    Also fixes a small inconsistency from the original get_status():
    the Ollama check was hardcoded to "http://localhost:11434" instead
    of respecting the configurable OLLAMA_HOST.
    """
    try:
        client = get_qdrant_client()
        stats = get_collection_stats(client)
        qdrant_line = (
            f'<span class="status-dot done"></span>Qdrant — {stats.points_count} vectors'
            if stats.exists else
            '<span class="status-dot error"></span>Qdrant — collection not found yet'
        )
    except Exception:
        qdrant_line = '<span class="status-dot error"></span>Qdrant — offline'

    try:
        httpx.get(OLLAMA_HOST, timeout=2)
        ollama_line = '<span class="status-dot done"></span>Ollama — online'
    except Exception:
        ollama_line = '<span class="status-dot error"></span>Ollama — offline'

    return (
        f'<div class="status-bar">{qdrant_line}<br>{ollama_line}</div>'
        f"<p><strong>LLM</strong> <code>{LLM_MODEL}</code><br>"
        f"<strong>Embed</strong> <code>{EMBED_MODEL}</code><br>"
        f"<strong>Chunk</strong> {CHUNK_SIZE} tokens (+{CHUNK_OVERLAP} overlap)</p>"
    )


def build_ui(query_service: QueryService, ingest_service: IngestService) -> gr.Blocks:
    """Build the full Gradio app, wired to the given service instances."""
    with gr.Blocks(title="Research Library") as app:

        gr.HTML(HEADER_HTML)

        with gr.Row():
            with gr.Column(scale=4):
                build_search_tab(query_service)
                paper_dropdown = build_summarize_tab(query_service)
                build_upload_tab(ingest_service, query_service, paper_dropdown)

            with gr.Column(scale=1):
                gr.Markdown("### System")
                status_box = gr.HTML(_get_system_status_html())
                status_refresh = gr.Button("Refresh", size="sm")
                status_refresh.click(fn=_get_system_status_html, outputs=status_box)

                gr.Markdown("---")
                gr.Markdown(HOW_TO_USE)

    return app