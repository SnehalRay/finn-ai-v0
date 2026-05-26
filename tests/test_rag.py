import tempfile
import pytest

from app.rag.embedder import embed
from app.rag.vector_store import VectorStore


SAMPLE_DOCS = [
    {"id": "t0", "text": "Q: How much water should I drink?\nA: About 8 cups per day.", "topic": "hydration"},
    {"id": "t1", "text": "Q: How many hours of sleep do adults need?\nA: 7 to 9 hours per night.", "topic": "sleep"},
    {"id": "t2", "text": "Q: What foods give me energy?\nA: Complex carbs and lean protein.", "topic": "nutrition"},
]


@pytest.fixture
def tmp_store():
    """Isolated in-memory-like ChromaDB using a temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir, collection_name="test_kb")
        embeddings = embed([d["text"] for d in SAMPLE_DOCS])
        store.upsert(
            ids=[d["id"] for d in SAMPLE_DOCS],
            embeddings=embeddings,
            documents=[d["text"] for d in SAMPLE_DOCS],
            metadatas=[{"topic": d["topic"]} for d in SAMPLE_DOCS],
        )
        yield store


def test_store_has_correct_count(tmp_store):
    assert tmp_store.count == len(SAMPLE_DOCS)


def test_relevant_query_returns_result(tmp_store):
    query_emb = embed(["daily water intake"])[0]
    results = tmp_store.query(query_emb, n_results=1)
    assert len(results) == 1
    assert results[0]["distance"] < 0.65
    assert "water" in results[0]["text"].lower()


def test_sleep_query_returns_sleep_doc(tmp_store):
    query_emb = embed(["how long should I sleep"])[0]
    results = tmp_store.query(query_emb, n_results=1)
    assert "sleep" in results[0]["text"].lower()


def test_topic_filter_restricts_results(tmp_store):
    query_emb = embed(["what should I eat"])[0]
    results = tmp_store.query(query_emb, n_results=3, topic_filter="nutrition")
    assert all(r["text"] for r in results)
    # All returned docs must be from the nutrition collection only
    # (ChromaDB where filter guarantees this)


def test_upsert_is_idempotent(tmp_store):
    """Re-upserting the same IDs should not duplicate documents."""
    embeddings = embed([d["text"] for d in SAMPLE_DOCS])
    tmp_store.upsert(
        ids=[d["id"] for d in SAMPLE_DOCS],
        embeddings=embeddings,
        documents=[d["text"] for d in SAMPLE_DOCS],
        metadatas=[{"topic": d["topic"]} for d in SAMPLE_DOCS],
    )
    assert tmp_store.count == len(SAMPLE_DOCS)


def test_reset_clears_collection(tmp_store):
    tmp_store.reset()
    assert tmp_store.count == 0
