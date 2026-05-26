from sentence_transformers import SentenceTransformer
from app.config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[embedder] Loading '{settings.EMBEDDING_MODEL}' (first run downloads ~80MB)...")
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts, convert_to_numpy=True).tolist()
