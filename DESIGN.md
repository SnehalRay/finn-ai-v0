# Finn — Architecture & Design

## Architecture Overview

```
                        POST /chat
                             │
                             ▼
                    ┌─────────────────┐
                    │  FastAPI + CORS  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  PII Sanitizer  │  strips phone, email, SSN, card
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │    Greeter      │  GREETING / FAREWELL / CONTINUE
                    └────────┬────────┘
                         is_social?
                         │       │
                       YES       NO
                         │       │
                    warm reply   ▼
                        ┌─────────────────┐
                        │   Guardrails    │  WELLNESS / MEDICAL / CRISIS / OTHER
                        └────────┬────────┘
                            blocked?
                            │       │
                           YES       NO
                            │       │
                      fixed/dynamic   ▼
                      response  ┌─────────────────┐
                                │  RAG Retriever  │  embed → cosine search → threshold
                                └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │  History Loader  │  last 6 messages from SQLite
                                └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │  Prompt Builder  │  injects RAG context
                                └────────┬────────┘
                                         │
                                         ▼
                                ┌─────────────────┐
                                │   Ollama LLM    │  llama3.2, local
                                └────────┬────────┘
                                         │
                                         ▼
                                    Response + SQLite save
```

---

## Component Responsibilities

### FastAPI Layer (`app/api/`)
Handles HTTP concerns only: request parsing, response shaping, CORS, and request ID tracing. No business logic lives here. Every route depends on `FinnAgent` via FastAPI's `Depends()` injection — making routes independently testable with a mock agent.

### PII Sanitizer (`app/privacy/sanitizer.py`)
Runs before any persistence or LLM call. Scrubs US phone numbers, email addresses, Social Security Numbers, and credit card numbers with regex patterns. This ensures PII never enters SQLite or the LLM context. The vector store is also safe by design — it only holds the curated knowledge base, never user messages.

### Greeter (`app/agent/greeter.py`)
Classifies messages as GREETING, FAREWELL, or CONTINUE before guardrails run. This prevents "hi" from burning a full RAG + LLM call and ensures social openers get a warm, consistent introduction. Uses a three-tier approach: O(1) token fast-path for unambiguous single words, then an LLM call for longer messages. The LLM classifier is intentionally conservative — any message with personal state or emotional content is always CONTINUE.

### Guardrails (`app/agent/guardrails.py`)
LLM-based content safety classifier. Four categories:
- **WELLNESS** — pass through to the agent loop
- **MEDICAL** — user asking Finn to diagnose or prescribe; redirect to healthcare provider
- **CRISIS** — active self-harm intent; return fixed response with crisis hotlines (988, Crisis Text Line)
- **OTHER** — off-topic; generate a contextual redirect, clarification request, or polite decline

CRISIS and MEDICAL use hand-written, safety-reviewed responses. OTHER uses a dynamic LLM response so Finn can redirect recipe questions to nutrition, ask about ambiguous "routine" questions, or cleanly decline finance queries — all contextually.

No regex patterns are used. Regex cannot distinguish "I was diagnosed with anxiety" (WELLNESS — sharing a story) from "Can you diagnose my anxiety?" (MEDICAL — asking Finn to act as a clinician). The LLM handles these nuances correctly with well-chosen few-shot examples in the prompt.

### RAG Pipeline (`app/rag/`)
Three components: `embedder.py` (SentenceTransformer singleton), `vector_store.py` (ChromaDB PersistentClient), `retriever.py` (embed + cosine search + distance threshold).

Retrieval works at the query level: the user's message is embedded and the nearest knowledge base chunks are returned if their cosine distance falls below `RAG_DISTANCE_THRESHOLD` (default 0.65). The context string is injected into Finn's system prompt. If nothing relevant is found, Finn still responds — just without RAG grounding.

### Agent Loop (`app/agent/finn.py`)
Wires all layers together in a fixed step order. The `FinnAgent.chat()` method is the single entry point for the entire pipeline. State (session, messages) lives in SQLite. The agent does not hold any in-memory state between requests.

### LLM Adapter (`app/llm/`)
An abstract base class (`LLMAdapter`) with a single `async complete(system, messages, max_tokens) -> str` method. The only concrete implementation is `OllamaAdapter`, which POSTs to the local Ollama server. This is the extensibility seam: swapping to a cloud LLM (Claude, OpenAI, Gemini) means implementing one method in one new class, with zero changes to the agent loop or any other layer.

---

## Knowledge Base

Two sources, merged at ingest time:

| Source | Content | Size |
|---|---|---|
| Kaggle Mental Health FAQ | 98 Q&A pairs — anxiety, depression, stress, therapy, stigma | 98 docs |
| `knowledge_base/docs/seed_wellness.md` | Hand-authored Q&A — nutrition, hydration, sleep, exercise | 20 docs |

Total: 118 documents. Each document is one Q&A pair stored as a single ChromaDB entry. Topic metadata (`nutrition`, `sleep`, `mental_health`, etc.) is stored alongside the embedding for optional topic-filtered retrieval.

**Why Q&A chunking?** Each chunk is self-contained: question + answer together give the embedding model the full semantic meaning. Splitting answer from question would halve the semantic density and degrade retrieval quality.

**Embedding model: `all-MiniLM-L6-v2`**
22M parameters, MIT licensed, CPU-fast (~10ms per query). The entire model is ~80MB. ChromaDB uses cosine distance with HNSW indexing for sub-millisecond approximate nearest-neighbour search over 118 documents.

---

## Privacy Model

| Data | Where it lives | PII present? |
|---|---|---|
| User messages | SQLite (`messages` table) | No — scrubbed before save |
| LLM context window | In-memory, not persisted | No — scrubbed input |
| Vector store | ChromaDB (`chroma_db/`) | No — only curated KB, never user messages |
| `user_id` | SQLite (`sessions` table) | No — opaque identifier from the caller |
| Logs | stdout only | No — messages not logged |

Both `finn.db` and `chroma_db/` are excluded from git.

---

## Design Decisions

### Why Ollama (local LLM) over a cloud API

Every evaluator can run the project cold without an API key, account, or internet connection after initial setup. Model quality is sufficient for wellness Q&A. The `LLMAdapter` ABC means a cloud swap is a one-class change whenever needed.

### Why LLM-only guardrails (no regex Stage 1)

Regex is too blunt for wellness conversation. Consider:
- `"I was diagnosed with anxiety last year"` — contains "diagnose" but is WELLNESS
- `"Can you diagnose my symptoms?"` — contains "diagnose" and is MEDICAL

A regex matching `diagnose` would block the first message. The LLM with few-shot examples gets both right. Since Ollama is local and free, the extra LLM call costs nothing. Accuracy wins.

### Why a dedicated Greeter (not part of guardrails)

Guardrails is about content safety. Greetings are not unsafe — they are a different problem (routing social openers efficiently). Mixing them would make guardrails responsible for two unrelated concerns and harder to test independently. The greeter is a thin, focused layer that only costs an LLM call for longer ambiguous messages; common tokens like "hi" and "bye" are resolved in O(1) with no LLM call.

### Why SQLite (not Postgres)

v0 has one server, no horizontal scale, and no concurrent write pressure that SQLite cannot handle. Adding a Postgres container for a demo project imposes setup friction with zero benefit. The schema and queries are standard SQL — migration to Postgres is a connection-string change and a driver swap.

### RAG distance threshold: 0.65

Empirically tuned. At 0.5, semantically related queries like "I feel anxious all the time" returned no results against the anxiety FAQ (distance ~0.54). At 0.65, relevant results are included while noise is still filtered. For context: cosine distance 0 = identical vectors, 1 = orthogonal, 2 = perfectly opposite.

---

## v0 Limitations

| Limitation | Notes |
|---|---|
| No authentication | `user_id` is caller-supplied; any client can impersonate any user |
| No rate limiting | Unbounded requests per IP/user |
| PII regex is not exhaustive | Catches common US formats; international phone numbers, government IDs from other countries are not covered |
| Single Ollama instance | All requests share one model — no load balancing |
| SQLite write serialisation | Module-level lock means high concurrency would queue writes |
| No message encryption at rest | SQLite DB is plaintext on disk |

---

## v0 → v1+ Scaling Path

| Layer | v0 | v1+ |
|---|---|---|
| LLM | Ollama (local llama3.2) | Swap `LLMAdapter` for Claude / GPT-4o; add model routing by query type |
| Vector store | ChromaDB (single node) | Pinecone or Weaviate (managed, horizontal scale) |
| Session storage | SQLite | Postgres with connection pooling (pgBouncer) |
| Auth | None | OAuth2 / JWT; `user_id` becomes a verified claim, not a free parameter |
| Rate limiting | None | Redis token bucket per `user_id`; FastAPI middleware |
| PII | Regex scrubbing | Microsoft Presidio or AWS Comprehend Medical for comprehensive detection |
| Knowledge base | Static CSV + seed file | Admin UI for curators; versioned KB with ingest pipeline |
| Observability | Stdout logs | Structured JSON logging → OpenTelemetry → Grafana |

### Future extensibility: `UserContextProvider`

The agent loop has a clean injection point for wearable / health app data. A `UserContextProvider` interface would be called between history load and prompt build:

```python
class UserContextProvider(Protocol):
    async def get_context(self, user_id: str) -> dict: ...
```

Implementations could pull from Apple Health, Fitbit, or fini's own health data store. The agent injects this as a second context block in the system prompt — no changes needed to guardrails, RAG, or the LLM adapter. The agent loop does not need to know where the data came from.

---

## Test Coverage

28 tests across three files:

| File | What it tests |
|---|---|
| `tests/test_guardrails.py` | Category routing (WELLNESS / MEDICAL / CRISIS / OTHER), hotline text in CRISIS response, provider redirect in MEDICAL, malformed LLM output normalisation |
| `tests/test_rag.py` | Ingest → query round-trip in isolated temp ChromaDB; distance threshold filtering |
| `tests/test_api.py` | POST /chat happy path, blocked message response shape, history endpoint, multi-turn session continuity |

All tests use a `MockLLMAdapter` that returns a fixed string — no Ollama dependency needed to run the suite.

```bash
python3 -m pytest tests/ -v
```
