"""
config.py — Centralized configuration for the Research Paper Summarizer
=========================================================================
Single source of truth for every setting used across ingestion, querying,
and the UI. No other module should redefine these constants — import them
from here instead. Every value can be overridden via environment variable
(loaded automatically from .env).
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────
PAPERS_DIR = Path(os.getenv("PAPERS_DIR", "papers"))

# ── Qdrant ────────────────────────────────────────────────────────────────
QDRANT_HOST     = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT     = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "papers")

# ── Ollama / models ──────────────────────────────────────────────────────
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
EMBED_DIM   = int(os.getenv("EMBED_DIM", 768))   # must match EMBED_MODEL's output dim
LLM_MODEL   = os.getenv("LLM_MODEL", "phi3:mini")

# ── Chunking (ingestion) ─────────────────────────────────────────────────
CHUNK_SIZE    = int(os.getenv("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))

# ── Retrieval (query) ────────────────────────────────────────────────────
TOP_K_SEARCH    = int(os.getenv("TOP_K_SEARCH", 3))    # chunks for cross-paper search
TOP_K_SUMMARIZE = int(os.getenv("TOP_K_SUMMARIZE", 4)) # chunks for single-paper summary

# ── LLM runtime options ─────────────────────────────────────────────────
# NOTE: original ingest.py used request_timeout=120 while query.py used 600.
# Standardized to the longer value here since cold-start reloads on
# Codespaces can take 2-3 min; override per-call if ingestion ever needs
# a shorter timeout.
LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", 600))
LLM_NUM_CTX         = int(os.getenv("LLM_NUM_CTX", 1024))   # kept low to avoid Codespaces OOM
LLM_NUM_PREDICT     = int(os.getenv("LLM_NUM_PREDICT", 512))
LLM_KEEP_ALIVE      = os.getenv("LLM_KEEP_ALIVE", "60m")
LLM_TEMPERATURE     = float(os.getenv("LLM_TEMPERATURE", 0.1))

# ── Keepalive ────────────────────────────────────────────────────────────
KEEPALIVE_INTERVAL_SEC = int(os.getenv("KEEPALIVE_INTERVAL_SEC", 240))
