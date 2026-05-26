import chromadb
from app.config import settings

_store: "VectorStore | None" = None


class VectorStore:
    def __init__(self, persist_dir: str, collection_name: str = "wellness_kb"):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        embedding: list[float],
        n_results: int = 3,
        topic_filter: str | None = None,
    ) -> list[dict]:
        where = {"topic": topic_filter} if topic_filter else None
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            where=where,
            include=["documents", "distances"],
        )
        docs = results["documents"][0]
        distances = results["distances"][0]
        return [{"text": d, "distance": dist} for d, dist in zip(docs, distances)]

    def reset(self) -> None:
        name = self._collection.name
        self._client.delete_collection(name)
        self._collection = self._client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(persist_dir=settings.CHROMA_PERSIST_DIR)
    return _store
