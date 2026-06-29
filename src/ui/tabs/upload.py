"""
ui/tabs/upload.py — "Upload new paper" tab
===============================================
Live ingestion from the UI. Wires Gradio components to
IngestService.ingest_papers() — no LlamaIndex/Qdrant logic lives here.

Calls refresh_paper_list() from summarize.py after a successful ingest
so the newly-added paper shows up in the Summarize dropdown immediately
— the same cross-tab refresh the original app.py did.
"""

import os
import time

import gradio as gr

from config import PAPERS_DIR
from services.ingest_service import IngestService
from services.query_service import QueryService
from ui.tabs.summarize import refresh_paper_list


def build_upload_tab(
    ingest_service: IngestService,
    query_service: QueryService,
    paper_dropdown: gr.Dropdown,
) -> None:
    """Create the Upload tab; refreshes `paper_dropdown` after each ingest."""
    with gr.Tab("Upload new paper"):
        gr.Markdown(
            "Upload PDFs to index them **live** — no restart needed. "
            "They appear in the Summarize dropdown immediately."
        )
        upload_input = gr.File(
            label="Drop PDFs here",
            file_types=[".pdf"],
            file_count="multiple",
        )
        upload_btn = gr.Button("Index papers", variant="primary")
        upload_status = gr.HTML(elem_classes=["status-bar"], value="")

        def _handle_upload(files):
            if not files:
                yield (
                    '<p class="citation-empty">Drop PDFs above to add them to your library.</p>',
                    refresh_paper_list(query_service),
                    gr.update(value="Index papers", variant="primary", interactive=True),
                )
                return

            yield (
                '<span class="status-dot busy"></span>Saving and indexing PDFs…',
                gr.update(),
                gr.update(value="Indexing…", variant="secondary", interactive=False),
            )

            PAPERS_DIR.mkdir(exist_ok=True)
            saved_paths = []
            for f in files:
                dest = PAPERS_DIR / os.path.basename(f.name)
                with open(f.name, "rb") as src, open(dest, "wb") as dst:
                    dst.write(src.read())
                saved_paths.append(dest)

            try:
                t0 = time.time()
                result = ingest_service.ingest_papers(saved_paths)
                elapsed = round(time.time() - t0, 1)
                names = ", ".join(p.name for p in saved_paths)
                status = (
                    '<span class="status-dot done"></span>'
                    f"Indexed <strong>{len(saved_paths)}</strong> file(s) in <strong>{elapsed}s</strong><br>"
                    f"Files: {names}<br>"
                    f"Chunks created: {result.node_count}<br>"
                    "Switch to <strong>Search</strong> or <strong>Summarize</strong> to query them."
                )
            except Exception as e:
                status = f'<span class="status-dot error"></span>Couldn&rsquo;t index these files: {e}'

            yield (
                status,
                refresh_paper_list(query_service),
                gr.update(value="Index papers", variant="primary", interactive=True),
            )

        upload_btn.click(
            fn=_handle_upload,
            inputs=upload_input,
            outputs=[upload_status, paper_dropdown, upload_btn],
        )