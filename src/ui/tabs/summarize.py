"""
ui/tabs/summarize.py — "Summarize a paper" tab
==================================================
Deep single-paper summarization. Wires Gradio components to
QueryService.summarize() / .list_papers() — no LlamaIndex/Qdrant logic
lives here.

refresh_paper_list() is exported (not private) because upload.py needs
to call it too, to repopulate this tab's dropdown right after a live
ingest — the same cross-tab dependency existed in the original app.py,
just within one function instead of two modules.
"""

import gradio as gr

from services.query_service import QueryService
from ui.formatters import format_elapsed, format_sources_html, format_status

_NO_SOURCES = '<p class="citation-empty">No sources retrieved yet.</p>'


def refresh_paper_list(query_service: QueryService) -> gr.Dropdown:
    """Rebuild the paper dropdown from whatever's currently indexed in Qdrant."""
    papers = query_service.list_papers()
    if not papers:
        return gr.Dropdown(
            choices=[], value=None, label="Select paper",
            info="No papers indexed yet — use the Upload tab",
        )
    return gr.Dropdown(
        choices=papers, value=papers[0], label="Select paper",
        info=f"{len(papers)} paper(s) indexed",
    )


def build_summarize_tab(query_service: QueryService) -> gr.Dropdown:
    """
    Create the Summarize tab. Returns the paper_dropdown component so
    the Upload tab can target it when refreshing after a live ingest.
    """
    with gr.Tab("Summarize a paper"):
        gr.Markdown(
            "Deep-dive into a single paper. "
            "Retrieves several chunks and builds a structured summary."
        )
        with gr.Row():
            paper_dropdown = gr.Dropdown(
                choices=query_service.list_papers(),
                label="Select paper",
                info="Click 'Refresh' after uploading a new paper",
                scale=3,
            )
            refresh_btn = gr.Button("Refresh list", scale=1)

        summary_input = gr.Textbox(
            label="Question / focus (optional)",
            placeholder="e.g. Summarize this paper.  /  What methodology was used?",
            value="Summarize this paper.",
            lines=2,
        )
        with gr.Row():
            summary_btn = gr.Button("Summarize", variant="primary")
            summary_clear = gr.Button("Clear")

        summary_meta = gr.HTML(elem_classes=["status-bar"], value="")
        summary_answer = gr.Markdown(label="Summary")
        summary_sources = gr.HTML(label="Sources", value=_NO_SOURCES)

        def _handle_summarize(filename: str, question: str):
            if not filename:
                yield (
                    "",
                    _NO_SOURCES,
                    format_status("idle", "Select a paper above"),
                    gr.update(value="Summarize", variant="primary", interactive=True),
                )
                return

            focus = question.strip() or "Summarize this paper."

            yield (
                "",
                "",
                format_status("busy", f"Retrieving chunks from {filename}…"),
                gr.update(value="Summarizing…", variant="secondary", interactive=False),
            )

            accumulated = ""
            for token, sources, elapsed, is_done in query_service.summarize(filename, focus):
                if not is_done:
                    accumulated += token
                    yield (
                        accumulated,
                        "",
                        format_status("busy", f"Generating… {elapsed}s elapsed"),
                        gr.update(value="Summarizing…", variant="secondary", interactive=False),
                    )
                else:
                    yield (
                        accumulated,
                        format_sources_html(sources),
                        format_status("done", f"Summarized in {format_elapsed(elapsed)}"),
                        gr.update(value="Summarize", variant="primary", interactive=True),
                    )

        summary_btn.click(
            fn=_handle_summarize,
            inputs=[paper_dropdown, summary_input],
            outputs=[summary_answer, summary_sources, summary_meta, summary_btn],
        )
        summary_clear.click(
            fn=lambda: (
                "", _NO_SOURCES, "",
                gr.update(value="Summarize", variant="primary", interactive=True),
            ),
            outputs=[summary_answer, summary_sources, summary_meta, summary_btn],
        )
        refresh_btn.click(fn=lambda: refresh_paper_list(query_service), outputs=paper_dropdown)

    return paper_dropdown