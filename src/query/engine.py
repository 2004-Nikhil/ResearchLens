"""
query/engine.py — build configured query engines
====================================================
Owns exactly one responsibility: turning a VectorStoreIndex into a
ready-to-query engine for either mode (cross-paper search, or
single-paper summarize). Also owns the one place that configures
LlamaIndex's global Settings for the *query* side — ingestion has its
own, separate configure_embed_settings() in ingestion/embedder.py, and
the two are intentionally kept apart (see embedder.py's docstring for
the bug that came from mixing them).

Does NOT run any queries or stream any tokens — that's runner.py's job.
Does NOT cache or own a long-lived index instance — that singleton
lifecycle belongs to services/query_service.py (not built yet).
"""

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.vector_stores import FilterOperator, MetadataFilter, MetadataFilters
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import (
    EMBED_MODEL,
    LLM_KEEP_ALIVE,
    LLM_MODEL,
    LLM_NUM_CTX,
    LLM_NUM_PREDICT,
    LLM_REQUEST_TIMEOUT,
    LLM_TEMPERATURE,
    OLLAMA_HOST,
    TOP_K_SEARCH,
    TOP_K_SUMMARIZE,
)
from query.prompts import SEARCH_PROMPT, SUMMARY_PROMPT
from storage.qdrant_client import get_client_and_store


def configure_llm_settings() -> None:
    """
    Configure LlamaIndex's global Settings for querying: embed model (to
    embed the incoming question) + LLM (to generate the answer).

    The num_ctx/num_predict caps are deliberate -- Ollama's default num_ctx
    is 32768, which needs ~48 GB of KV cache and OOMs on Codespaces. 1024
    is enough for 3-4 chunks of 512 tokens each.
    """
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_HOST,
    )
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_HOST,
        request_timeout=LLM_REQUEST_TIMEOUT,
        temperature=LLM_TEMPERATURE,
        additional_kwargs={
            "num_ctx": LLM_NUM_CTX,
            "num_predict": LLM_NUM_PREDICT,
            "keep_alive": LLM_KEEP_ALIVE,
        },
    )


def build_index(vector_store: QdrantVectorStore | None = None) -> VectorStoreIndex:
    """
    Wrap a QdrantVectorStore in a LlamaIndex VectorStoreIndex. If no
    vector_store is given, connects via storage.qdrant_client using the
    default collection from config.
    """
    if vector_store is None:
        _, vector_store = get_client_and_store()
    return VectorStoreIndex.from_vector_store(vector_store=vector_store)


def build_search_engine(index: VectorStoreIndex):
    """Query engine for cross-paper semantic search (streaming, compact)."""
    return index.as_query_engine(
        similarity_top_k=TOP_K_SEARCH,
        response_mode="compact",
        streaming=True,
        text_qa_template=SEARCH_PROMPT,
        node_postprocessors=[],
    )


def build_summarize_engine(index: VectorStoreIndex, filename: str):
    """Query engine for deep summarization of a single paper, filtered by filename."""
    filters = MetadataFilters(filters=[
        MetadataFilter(
            key="file_name",
            value=filename,
            operator=FilterOperator.EQ,
        )
    ])
    return index.as_query_engine(
        similarity_top_k=TOP_K_SUMMARIZE,
        response_mode="compact",
        streaming=True,
        text_qa_template=SUMMARY_PROMPT,
        filters=filters,
        node_postprocessors=[],
    )
