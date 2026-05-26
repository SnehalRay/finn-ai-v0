"""
Ingest knowledge base into ChromaDB.
Sources:
  1. knowledge_base/data/Mental_Health_FAQ.csv  (Kaggle: narendrageek/mental-health-faq-for-chatbot)
  2. knowledge_base/docs/seed_wellness.md        (hand-authored: nutrition, sleep, hydration, exercise)

Usage:
  python -m knowledge_base.ingest          # incremental upsert
  python -m knowledge_base.ingest --reset  # wipe collection first
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.rag.embedder import embed
from app.rag.vector_store import get_vector_store


SEED_PATH = Path(__file__).parent / "docs" / "seed_wellness.md"
CSV_PATH = Path(__file__).parent / "data" / "Mental_Health_FAQ.csv"


def _load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        print(f"[ingest] CSV not found at {CSV_PATH} — skipping.")
        return []
    docs = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f)):
            q = row["Questions"].strip()
            a = row["Answers"].strip()
            if q and a:
                docs.append({
                    "id": f"mh_faq_{i}",
                    "text": f"Q: {q}\nA: {a}",
                    "topic": "mental_wellness",
                })
    print(f"[ingest] Loaded {len(docs)} rows from Mental_Health_FAQ.csv")
    return docs


def _load_seed() -> list[dict]:
    if not SEED_PATH.exists():
        print(f"[ingest] Seed file not found at {SEED_PATH} — skipping.")
        return []

    TOPIC_KEYWORDS = {
        "nutrition": ["protein", "carb", "fat", "vitamin", "fibre", "fiber", "calori", "diet", "food", "eat", "meal", "nutrient", "fasting"],
        "sleep": ["sleep", "insomnia", "groggy", "circadian", "nap", "rest", "wake"],
        "hydration": ["water", "hydrat", "fluid", "dehydrat", "electrolyte", "drink"],
        "exercise": ["exercise", "workout", "cardio", "hiit", "step", "walk", "strength", "muscle", "fitness", "training"],
        "mental_wellness": ["stress", "mood", "mental", "breath", "meditat", "anxiety", "wellbeing", "mindful"],
    }

    def _detect_topic(text: str) -> str:
        lower = text.lower()
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in lower for kw in keywords):
                return topic
        return "general"

    raw = SEED_PATH.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^## Q:)", raw, flags=re.MULTILINE)
    docs = []
    for i, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if not chunk.startswith("## Q:"):
            continue
        match = re.match(r"## Q:\s*(.+?)\nA:\s*(.+)", chunk, re.DOTALL)
        if not match:
            continue
        q = match.group(1).strip()
        a = match.group(2).strip()
        docs.append({
            "id": f"seed_{i}",
            "text": f"Q: {q}\nA: {a}",
            "topic": _detect_topic(q + " " + a),
        })
    print(f"[ingest] Loaded {len(docs)} entries from seed_wellness.md")
    return docs


def ingest(reset: bool = False) -> None:
    store = get_vector_store()

    if reset:
        store.reset()
        print("[ingest] Collection wiped.")

    docs = _load_csv() + _load_seed()
    if not docs:
        print("[ingest] No documents to ingest. Exiting.")
        return

    texts = [d["text"] for d in docs]
    print(f"[ingest] Embedding {len(texts)} documents...")
    embeddings = embed(texts)

    store.upsert(
        ids=[d["id"] for d in docs],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{"topic": d["topic"]} for d in docs],
    )
    print(f"[ingest] Done. {len(docs)} documents in ChromaDB.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Wipe collection before ingesting")
    args = parser.parse_args()
    ingest(reset=args.reset)
