"""
ui/tabs/search.py — "Search all papers" tab
===============================================
Cross-paper semantic search. Wires Gradio components to
QueryService.search() — no LlamaIndex/Qdrant logic lives here.
"""

import gradio as gr

from services.query_service import QueryService
from ui.formatters import format_elapsed, format_sources_html, format_status

EXAMPLE_SEARCHES = [
    "What problem does this paper solve?",
    "What blockchain standards are discussed?",
    "What are the key findings?",
    "What are the limitations of this research?",
    "How does tokenization benefit real estate?",
]

_EMPTY_HINT = '<p class="citation-empty">Type a question above to search your library.</p>'
_NO_SOURCES = '<p class="citation-empty">No sources retrieved yet.</p>'


def build_search_tab(query_service: QueryService) -> None:
    """Create the Search tab inside the currently-active gr.Blocks context."""
    with gr.Tab("Search all papers"):
        gr.Markdown(
            "Ask anything across your entire paper library. "
            "Best for discovery and cross-paper questions."
        )
        search_input = gr.Textbox(
            label="Question",
            placeholder="e.g. What is tokenization of RWAs?",
            lines=2,
        )
        with gr.Row():
            search_btn = gr.Button("Search", variant="primary")
            search_clear = gr.Button("Clear")

        gr.Examples(examples=EXAMPLE_SEARCHES, inputs=search_input, label="Example questions")

        search_meta = gr.HTML(elem_classes=["status-bar"], value="")
        search_answer = gr.Markdown(label="Answer")
        search_sources = gr.HTML(label="Sources", value=_NO_SOURCES)

        def _handle_search(query: str):
            if not query.strip():
                yield (
                    "",
                    _EMPTY_HINT,
                    format_status("idle", "Ask a question to begin"),
                    gr.update(value="Search", variant="primary", interactive=True),
                )
                return

            yield (
                "",
                "",
                format_status("busy", "Embedding your question and searching…"),
                gr.update(value="Searching…", variant="secondary", interactive=False),
            )

            accumulated = ""
            for token, sources, elapsed, is_done in query_service.search(query):
                if not is_done:
                    accumulated += token
                    yield (
                        accumulated,
                        "",
                        format_status("busy", f"Generating… {elapsed}s elapsed"),
                        gr.update(value="Searching…", variant="secondary", interactive=False),
                    )
                else:
                    yield (
                        accumulated,
                        format_sources_html(sources),
                        format_status("done", f"Answered in {format_elapsed(elapsed)}"),
                        gr.update(value="Search", variant="primary", interactive=True),
                    )

        search_btn.click(
            fn=_handle_search,
            inputs=search_input,
            outputs=[search_answer, search_sources, search_meta, search_btn],
        )
        search_clear.click(
            fn=lambda: (
                "", _NO_SOURCES, "",
                gr.update(value="Search", variant="primary", interactive=True),
            ),
            outputs=[search_answer, search_sources, search_meta, search_btn],
        )