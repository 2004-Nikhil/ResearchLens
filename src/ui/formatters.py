"""
ui/formatters.py — shared display formatting for the UI layer
===================================================================
Pure functions that turn query-service output into HTML/text the
Gradio components can render. No Gradio component creation here, no
event wiring — that's the tab modules' job.

format_sources_html() replaces the original _format_sources_list()
markdown table with "citation cards" — this app's signature visual
element. Filenames and excerpts come from PDF text, which can contain
stray HTML-special characters, so they're escaped before being
embedded in the HTML string.
"""

import html

from query.models import SourceNode


def format_elapsed(sec: float) -> str:
    """Render an elapsed-time float as a short human string."""
    if sec < 60:
        return f"{sec:.1f}s"
    return f"{int(sec // 60)}m {int(sec % 60)}s"


def format_status(stage: str, message: str) -> str:
    """
    Build the small colored-dot status line shown above an answer.
    `stage` is one of "busy", "done", "error", "idle" — anything else
    falls back to "idle".
    """
    dot_class = stage if stage in ("busy", "done", "error") else "idle"
    return f'<span class="status-dot {dot_class}"></span>{html.escape(message)}'


def format_sources_html(sources: list[SourceNode]) -> str:
    """
    Render retrieved sources as citation cards: relevance score and page
    in monospace (this is data, not prose), the section it came from as
    a small tag, and an italic excerpt. Returns a complete HTML string
    for a gr.HTML component.
    """
    if not sources:
        return '<p class="citation-empty">No sources retrieved yet.</p>'

    cards = []
    for s in sources:
        section_class = "section-abstract" if s.section == "abstract" else "section-body"
        filename = html.escape(s.filename)
        section = html.escape(s.section)
        preview = html.escape(s.preview)
        cards.append(
            f'<div class="citation-card {section_class}">'
            f'<div class="citation-meta">'
            f'<div class="score">{s.score:.3f}</div>'
            f'<div>p.{s.page}</div>'
            f'</div>'
            f'<div class="citation-body">'
            f'<span class="citation-file">{filename}</span>'
            f'<span class="citation-tag">{section}</span>'
            f'<div class="citation-preview">&ldquo;{preview}&hellip;&rdquo;</div>'
            f'</div>'
            f'</div>'
        )
    return f'<div class="citation-list">{"".join(cards)}</div>'