# Finn — AI Wellness Bot (v0)

Finn is an AI-powered wellness companion built for the fini health app. Ask Finn anything about nutrition, hydration, sleep, exercise, or mental wellbeing and get grounded, evidence-based responses — powered entirely by local, open-source models.

---

## Prerequisites

Before running, make sure you have the following installed:

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | https://python.org |
| pip | latest | https://pip.pypa.io |
| Ollama | latest | https://ollama.com |
| Node.js + npm | 18+ | https://nodejs.org |

---

## Quick Start

Clone the repo and run the setup script. It handles everything — dependencies, model download, and knowledge base ingestion.

```bash
git clone https://github.com/SnehalRay/finn.ai-v0.git
cd finn.ai-v0
bash scripts/start.sh
```

Once running:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

Press `Ctrl+C` to stop both servers.

---

## Manual Setup (step by step)

If you prefer to run things manually:

**1. Install Python dependencies**
```bash
pip3 install -r requirements.txt
```

**2. Install frontend dependencies**
```bash
cd frontend && npm install && cd ..
```

**3. Pull the Ollama model**
```bash
ollama pull llama3.2
```

**4. Build the knowledge base**
```bash
python3 -m knowledge_base.ingest --reset
```

**5. Start the backend**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**6. Start the frontend (new terminal)**
```bash
cd frontend && npm run dev
```

---

## Using Make

A `Makefile` is included for common tasks:

```bash
make setup         # first-time: install deps + pull model + ingest KB
make run           # start backend + frontend
make run-backend   # start API only (port 8000)
make run-frontend  # start frontend only (port 5173)
make test          # run test suite
make ingest        # rebuild knowledge base
make clean         # stop servers + wipe local DB and vector store
```

---

## API Reference

### POST /chat

Send a message to Finn.

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "alice", "message": "How much water should I drink daily?"}'
```

```json
{
  "session_id": "c14af2ff-...",
  "message": "Most adults need about 8-10 cups (2-2.5 litres) per day...",
  "blocked": false,
  "block_reason": null,
  "sources_used": true
}
```

Pass `session_id` in subsequent messages to continue the same conversation.

---

### GET /chat/history/{session_id}

Retrieve the full conversation history for a session.

```bash
curl http://localhost:8000/chat/history/c14af2ff-...
```

---

### GET /health

Liveness check.

```bash
curl http://localhost:8000/health
# {"status": "ok", "agent": "Finn v0"}
```

---

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Model to use (e.g. `mistral`, `phi3`) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence-transformers model for RAG |
| `CHROMA_PERSIST_DIR` | `./chroma_db` | Where ChromaDB stores vectors |
| `SQLITE_DB_PATH` | `./finn.db` | Session and message history |
| `MAX_CONTEXT_MESSAGES` | `6` | Conversation history window |
| `RAG_TOP_K` | `3` | Number of knowledge base results to retrieve |
| `RAG_DISTANCE_THRESHOLD` | `0.65` | Cosine distance cutoff for relevance |

To switch models, update `OLLAMA_MODEL` and pull the new model:

```bash
ollama pull mistral
# then update OLLAMA_MODEL=mistral in .env
```

---

## Running Tests

```bash
make test
# or
python3 -m pytest tests/ -v
```

28 tests across guardrails, RAG pipeline, and API endpoints.

---

## Project Structure

```
finn.ai-v0/
├── app/
│   ├── agent/          # Finn orchestration loop, guardrails, greeter, prompts
│   ├── api/            # FastAPI routes and middleware
│   ├── db/             # SQLite session and message storage
│   ├── llm/            # Ollama adapter (LLMAdapter ABC)
│   ├── privacy/        # PII sanitizer
│   ├── rag/            # Embedder, ChromaDB vector store, retriever
│   ├── config.py       # All settings via pydantic-settings
│   └── main.py         # FastAPI app + lifespan startup
├── knowledge_base/
│   ├── data/           # Mental Health FAQ (Kaggle dataset, 98 Q&A pairs)
│   ├── docs/           # Seed wellness Q&A (nutrition, sleep, hydration, exercise)
│   └── ingest.py       # Builds ChromaDB from both sources
├── frontend/           # Vite + React frontend
├── tests/              # 28 pytest tests
├── scripts/
│   └── start.sh        # One-command setup and launch
└── Makefile
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| API | FastAPI + Uvicorn |
| LLM | Ollama (llama3.2, local) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector store | ChromaDB |
| Session storage | SQLite |
| Frontend | React + Vite |
