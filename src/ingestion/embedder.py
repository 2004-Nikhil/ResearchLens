"""
ingestion/embedder.py — embed nodes and upsert into the vector store
=======================================================================
Owns exactly one responsibility: turning TextNodes into vectors and
writing them into Qdrant via a QdrantVectorStore. Loading PDFs is
loader.py's job; chunking/metadata is chunker.py's job.

NOTE on a behavior change from the original ingest.py: the original
embed_and_store() also set `Settings.llm` here (with request_timeout=120
and no num_ctx/num_predict caps) — a different config than the one
query.py sets for querying (num_ctx=1024, explicitly tuned to avoid OOM
on Codespaces). Since Settings is a process-wide global, this meant any
live ingest in the same process (e.g. app.py's "Upload" tab) silently
overwrote the OOM-safe query settings. Embedding doesn't need an LLM at
all, so Settings.llm is intentionally not touched here — only the query
layer should own it.
"""

from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

from config import CHUNK_SIZE, EMBED_MODEL, OLLAMA_HOST


def build_embed_model() -> OllamaEmbedding:
    """Construct the Ollama embedding model used for all node embeddings."""
    return OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_HOST,
        ollama_additional_kwargs={"mirostat": 0},
    )


def configure_embed_settings(embed_model: OllamaEmbedding | None = None) -> None:
    """Point LlamaIndex's global Settings at our embed model + chunk size."""
    Settings.embed_model = embed_model or build_embed_model()
    Settings.chunk_size = CHUNK_SIZE


def embed_and_store(nodes: list[TextNode], store: QdrantVectorStore) -> VectorStoreIndex:
    """
    Embed all nodes and upsert them into Qdrant via `store`.
    Returns the VectorStoreIndex so it can be reused elsewhere if needed.
    """
    print(f"\n🔢  Embedding {len(nodes)} node(s) with '{EMBED_MODEL}'...")
    print("    (first run downloads the model — subsequent runs are instant)\n")

    configure_embed_settings()

    storage = StorageContext.from_defaults(vector_store=store)
    index = VectorStoreIndex(
        nodes,
        storage_context=storage,
        show_progress=True,
    )
    return index
