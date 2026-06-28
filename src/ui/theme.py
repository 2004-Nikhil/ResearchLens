"""
ui/theme.py — visual identity for the Research Library
===========================================================
A "library card catalog" identity: cool archival-paper tones, deep
fountain-pen ink and archive-binding teal for action/status, brass for
relevance precision, paired with a literary serif for headlines against
a technical monospace for data (scores, page numbers, filenames) — the
same contrast this tool itself draws, between the papers it reads and
the engineering doing the reading.

This is the one file that owns "what does it look like" — component
wiring lives in builder.py and the tab modules.

IMPORTANT — Gradio 6.0 API note (verified against gradio==6.19.0 in
testing): `theme` and `css` are no longer accepted by the gr.Blocks()
constructor; they moved to .launch(). So THEME and CSS are exported
here for the future app.py entry point to pass into
app.launch(theme=THEME, css=CSS, ...) — NOT into gr.Blocks(...).
builder.py only sets `title`, which still belongs on the constructor.
"""

import gradio as gr

# ── Design tokens ─────────────────────────────────────────────────────────
PAPER    = "#0F1115"   # background — deep archival charcoal
SURFACE  = "#1A1D24"   # cards/panels above the background

INK      = "#F3F4F6"   # primary text — soft white
INK_SOFT = "#A3ACB9"   # secondary text, captions

ARCHIVE  = "#4FAF9D"   # live/success status — brighter archival teal
BRASS    = "#D4A85A"   # relevance/precision accent — muted antique brass

ERROR    = "#E06666"   # accessible error red
LINE     = "#2B313C"   # subtle dividers/borders

THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.stone,
    font=[gr.themes.GoogleFont("IBM Plex Sans"), "ui-sans-serif", "system-ui"],
    font_mono=[gr.themes.GoogleFont("IBM Plex Mono"), "ui-monospace"],
).set(
    body_background_fill=PAPER,
    body_background_fill_dark=PAPER,   # force light palette even in dark mode --
                                        # the custom citation cards below assume it
    button_primary_background_fill=INK,
    button_primary_background_fill_hover=ARCHIVE,
    button_primary_text_color=SURFACE,
    block_background_fill=SURFACE,
    block_border_color=LINE,
    block_label_text_color=INK_SOFT,
)

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Spectral:wght@500;600&display=swap');

:root {{
    --paper: {PAPER};
    --surface: {SURFACE};
    --ink: {INK};
    --ink-soft: {INK_SOFT};
    --archive: {ARCHIVE};
    --brass: {BRASS};
    --error: {ERROR};
    --line: {LINE};
}}

/* ── Header / wordmark ──────────────────────────────────────────────── */
.app-eyebrow {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-soft);
    margin-bottom: 0.25rem;
}}
.app-title {{
    font-family: 'Spectral', serif;
    font-weight: 600;
    font-size: 2rem;
    color: var(--ink);
    margin: 0;
}}
.app-subtitle {{
    color: var(--ink-soft);
    font-size: 0.95rem;
    margin-top: 0.15rem;
}}

/* ── Status line (used in all three tabs + sidebar) ─────────────────── */
.status-bar {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    min-height: 1.4rem;
    color: var(--ink-soft);
}}
.status-dot {{
    display: inline-block;
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    margin-right: 0.45rem;
}}
.status-dot.busy  {{ background: var(--brass); animation: pulse 1.4s ease-in-out infinite; }}
.status-dot.done  {{ background: var(--archive); }}
.status-dot.error {{ background: var(--error); }}
.status-dot.idle  {{ background: var(--line); }}

@keyframes pulse {{
    0%, 100% {{ opacity: 1; }}
    50%      {{ opacity: 0.35; }}
}}

/* ── Citation cards — the signature element, replacing a plain table ── */
.citation-list {{
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.5rem;
}}
.citation-card {{
    display: flex;
    gap: 0.75rem;
    padding: 0.6rem 0.8rem;
    background: var(--surface);
    border: 1px solid var(--line);
    border-left: 3px solid var(--archive);
    border-radius: 6px;
}}
.citation-card.section-abstract {{ border-left-color: var(--brass); }}
.citation-meta {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--ink-soft);
    white-space: nowrap;
    min-width: 6rem;
}}
.citation-meta .score {{ color: var(--brass); font-weight: 600; }}
.citation-body {{ flex: 1; min-width: 0; }}
.citation-file {{
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: var(--ink);
    font-weight: 500;
}}
.citation-tag {{
    display: inline-block;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    color: var(--ink-soft);
    border: 1px solid var(--line);
    border-radius: 3px;
    padding: 0 0.3rem;
    margin-left: 0.4rem;
}}
.citation-preview {{
    font-size: 0.85rem;
    color: var(--ink-soft);
    font-style: italic;
    margin-top: 0.15rem;
}}
.citation-empty {{
    color: var(--ink-soft);
    font-size: 0.85rem;
    font-style: italic;
}}
"""