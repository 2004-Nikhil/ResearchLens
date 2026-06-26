"""
services/query_service.py — owns the long-lived query index + LLM lifecycle
================================================================================
This is where the global mutable state from the original query.py
actually goes: the old module-level `_settings_initialised` / `_index`
globals become attributes of one QueryService instance, created once in
app.py and handed to the UI tabs. warmup() and start_keepalive() (LLM
process lifecycle) live here too, since they're about keeping this
service's model loaded, not about running any individual query.
"""

import threading
import time

import httpx
from llama_index.core import VectorStoreIndex

from config import KEEPALIVE_INTERVAL_SEC, LLM_MODEL, OLLAMA_HOST
from query.engine import build_index, configure_llm_settings
from query.runner import search as run_search, summarize as run_summarize
from storage.collection import list_papers as list_indexed_papers
from storage.qdrant_client import get_qdrant_client


class QueryService:
    """
    Lazily builds and caches a single VectorStoreIndex + configured
    LlamaIndex Settings, then exposes search/summarize/list_papers/warmup
    on top of it. Create exactly one instance at app startup and reuse it
    everywhere -- that single instance is the explicit, named replacement
    for the old hidden module-level globals.
    """

    def __init__(self):
        self._settings_configured = False
        self._index: VectorStoreIndex | None = None
        self._keepalive_started = False

    # ── Lazy setup ──────────────────────────────────────────────────

    def _ensure_ready(self) -> VectorStoreIndex:
        """Configure Settings and build the index on first use; reuse after that."""
        if not self._settings_configured:
            configure_llm_settings()
            self._settings_configured = True
        if self._index is None:
            self._index = build_index()
        return self._index

    # ── Public query API ────────────────────────────────────────────

    def search(self, query: str):
        """Streaming semantic search across all indexed papers."""
        index = self._ensure_ready()
        yield from run_search(index, query)

    def summarize(self, filename: str, query: str = "Summarize this paper."):
        """Streaming summarization of a single paper."""
        index = self._ensure_ready()
        yield from run_summarize(index, filename, query)

    def list_papers(self) -> list[str]:
        """All unique paper filenames currently indexed in Qdrant."""
        client = get_qdrant_client()
        return list_indexed_papers(client)

    # ── LLM lifecycle ───────────────────────────────────────────────

    def warmup(self) -> bool:
        """
        Send a trivial prompt to Ollama to force the model into memory.
        Call once at app startup so the first real query isn't a cold start.
        """
        print(f"  Warming up {LLM_MODEL} (loading into Ollama memory)...")
        try:
            resp = httpx.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": LLM_MODEL,
                    "prompt": "Reply with the single word: ready",
                    "stream": False,
                    "options": {"num_ctx": 2048, "num_predict": 5},
                    "keep_alive": "60m",
                },
                timeout=600,
            )
            if resp.status_code == 200:
                print("  Model warm -- ready for queries.")
                return True
            print(f"  Warmup failed (HTTP {resp.status_code}): {resp.text[:200]}")
            return False
        except Exception as e:
            print(f"  Warmup failed: {e}")
            return False

    def start_keepalive(self, interval_sec: int = KEEPALIVE_INTERVAL_SEC) -> None:
        """
        Ping Ollama every `interval_sec` seconds so the model isn't evicted
        from memory between user queries. Runs in a daemon thread. Guarded
        against double-starting -- the original had no such guard, but
        since it's only ever called once at startup this changes nothing
        in practice.
        """
        if self._keepalive_started:
            return
        self._keepalive_started = True

        def _ping():
            while True:
                time.sleep(interval_sec)
                try:
                    httpx.post(
                        f"{OLLAMA_HOST}/api/generate",
                        json={
                            "model": LLM_MODEL,
                            "prompt": ".",
                            "stream": False,
                            "options": {"num_ctx": 2048, "num_predict": 1},
                            "keep_alive": "60m",
                        },
                        timeout=30,
                    )
                except Exception:
                    pass  # silent -- keepalive failures are non-fatal

        threading.Thread(target=_ping, daemon=True).start()
