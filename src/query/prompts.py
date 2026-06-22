"""
query/prompts.py — prompt templates for search and summarize modes
======================================================================
Pure prompt text, no logic. Tune wording here without touching how
query engines are built (engine.py) or how queries are executed
(runner.py).
"""

from llama_index.core.prompts import PromptTemplate

# Used by search mode -- concise, grounded answer with citations
SEARCH_PROMPT = PromptTemplate(
    "You are a research assistant helping a user explore academic papers.\n"
    "Answer the question below using ONLY the context provided.\n"
    "Be concise (3-5 sentences). If the context does not contain the answer, say so.\n"
    "At the end, note which paper(s) the answer came from.\n\n"
    "Context:\n{context_str}\n\n"
    "Question: {query_str}\n\n"
    "Answer:"
)

# Used by summarize mode -- structured breakdown of a single paper
SUMMARY_PROMPT = PromptTemplate(
    "You are an expert research analyst. Based on the excerpts below from a single paper,\n"
    "provide a structured summary with these exact sections:\n\n"
    "**TL;DR** (1 sentence)\n\n"
    "**Problem** (What gap or challenge does this paper address?)\n\n"
    "**Methodology** (How did the authors approach it?)\n\n"
    "**Key Findings** (What did they discover or build?)\n\n"
    "**Limitations** (What are the weaknesses or future work noted?)\n\n"
    "If a section cannot be determined from the excerpts, write 'Not mentioned in available text.'\n\n"
    "Paper excerpts:\n{context_str}\n\n"
    "Question/Focus: {query_str}\n\n"
    "Structured Summary:"
)
