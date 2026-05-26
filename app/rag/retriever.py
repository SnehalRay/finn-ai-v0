from app.rag.embedder import embed
from app.rag.vector_store import get_vector_store
from app.config import settings


def retrieve_context(query: str, topic_filter: str | None = None) -> str:
    """Embed query, search ChromaDB, return relevant context or empty string."""
    embedding = embed([query])[0]
    results = get_vector_store().query(
        embedding=embedding,
        n_results=settings.RAG_TOP_K,
        topic_filter=topic_filter,
    )
    relevant = [r for r in results if r["distance"] < settings.RAG_DISTANCE_THRESHOLD]
    if not relevant:
        return ""
    return "\n\n".join(r["text"] for r in relevant)
