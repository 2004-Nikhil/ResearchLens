"""
query/models.py — data models for query results
==================================================
Plain dataclasses with no behavior — describing the shape of a single
retrieved source chunk and the overall result of a search/summarize call.
Used by runner.py to build results and by the UI to display them.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SourceNode:
    filename: str
    section: str
    page: int
    score: float
    preview: str   # first 150 chars of the chunk


@dataclass
class QueryResult:
    answer: str
    mode: str             # "search" or "summarize"
    query: str
    sources: list[SourceNode] = field(default_factory=list)
    elapsed_sec: float = 0.0
    error: Optional[str] = None
