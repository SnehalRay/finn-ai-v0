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

The current stack is a single-machine pipeline where every layer is a sequential bottleneck:

```
Request → FastAPI (1 instance) → Ollama (1 thread) → ChromaDB (1 node) → SQLite (1 writer)
```

The sections below address each layer in order of impact.

---

### 1. LLM Layer — the primary bottleneck

Ollama with llama3.2 processes one request at a time on CPU. Under any real concurrent load this becomes the queue.

**Cloud LLM swap** — the `LLMAdapter` ABC already isolates this. Swapping to Claude, GPT-4o, or Gemini is one new class with no changes to the agent loop, guardrails, or RAG. Cost per request, but scales to any throughput.

**Model tiering** — the guardrails classifier calls the LLM on every message but only needs one word back (`WELLNESS`, `MEDICAL`, etc.). Use a cheap, fast model (e.g. Haiku, Flash) for classification and a smarter model for response generation. This cuts LLM cost by ~60% at scale with no quality loss on generation.

**Response streaming** — switch from request-response to SSE or WebSocket so users see tokens appear in real time. No change to throughput, but perceived latency drops dramatically. FastAPI natively supports `StreamingResponse`.

**GPU serving** — if staying local, serving Ollama on a GPU instance gives 10-20x throughput over CPU at modest cost.

---

### 2. Vector Store — ChromaDB is single-node

**Managed vector DB** — migrate to Pinecone, Weaviate, or Qdrant. All support horizontal scaling, namespaces (for multi-tenant KB isolation), and metadata filtering. The `VectorStore` wrapper in `app/rag/vector_store.py` isolates the ChromaDB dependency — replacing it is a class swap.

**pgvector** — if the rest of the stack moves to Postgres, `pgvector` keeps the vector store co-located with session storage, reducing operational overhead.

**RAG quality improvements:**
- **Hybrid search** — combine BM25 (keyword/sparse) with dense embeddings. Dense retrieval misses exact term matches; BM25 catches them. Union results and re-rank.
- **Cross-encoder re-ranking** — retrieve top-20, score with a cross-encoder, return top-5. Meaningful quality jump for short or ambiguous queries.
- **Feedback loop** — log which retrieved chunks appear in responses users engage with. Use this signal to fine-tune retrieval over time.

---

### 3. Session Storage — SQLite cannot scale writes

**Postgres** — the schema and queries are standard SQL. Migration is a connection-string change and a driver swap (`asyncpg`). Add **pgBouncer** for connection pooling — FastAPI coroutines each want a DB connection; without pooling you exhaust the limit quickly.

**Redis hot cache** — conversation history is read on every turn. Cache active sessions in Redis (write-through to Postgres). At steady load this cuts DB reads by ~80-90%.

**Message archival** — partition the `messages` table by time range and archive old conversations to cold storage (S3 + Athena for ad hoc queries). Active storage stays small.

---

### 4. API Layer — horizontal scaling

The agent loop is already stateless — all state lives in the DB. This means N API instances can run behind a load balancer with no code changes.

```
                    ALB / nginx
                   /     |     \
              API-1    API-2    API-3
                   \     |     /
               Postgres + Redis + Vector Store
```

Add an **API Gateway** in front for: rate limiting per `user_id`, TLS termination, JWT validation, and request logging. FastAPI middleware handles rate limiting if you're not using a gateway.

---

### 5. Auth — currently absent

`user_id` is a free string the client supplies — any caller can impersonate any user. For a real product:

- **JWT / OAuth2** — `user_id` becomes a verified claim in a signed token, not a client-supplied parameter.
- **Short-lived tokens** — rotated on each session, stored server-side, revocable.

Auth also unblocks user-level rate limiting, GDPR deletion requests, and per-user personalization.

---

### 6. Personalization — the product moat

Finn currently knows nothing about a user beyond the last 6 messages. A health app can build a durable advantage here by injecting user context between history load and prompt build:

```python
class UserContextProvider(Protocol):
    async def get_context(self, user_id: str) -> dict: ...
```

Implementations:
- **Wearable data** — Apple Health, Fitbit, Oura: sleep hours, HRV, step count. Finn can say "you only slept 5 hours last night — here's what that does to your focus" instead of giving generic advice.
- **User profile** — dietary preferences, fitness level, health goals collected at onboarding.
- **Long-term memory** — summarise past conversations into a persistent profile so Finn remembers context across sessions ("this user is training for a 5K", "has a dairy intolerance").

This slot is already designed into the agent loop — no changes needed to guardrails, RAG, or the LLM adapter.

---

### 7. Observability — invisible right now

Without instrumentation you cannot debug performance or quality at scale:

- **Structured logging** — every request logs `session_id`, `user_id`, per-stage latency (guardrails, RAG, LLM), `sources_used`, `blocked`. JSON format for log aggregation (Datadog, ELK).
- **OpenTelemetry traces** — distributed trace through the full pipeline; see exactly where latency lives per request.
- **LLM quality metrics** — guardrail false positive rate (wellness messages incorrectly blocked), RAG hit rate, session depth (do users send more than 2 messages?), response rating if you add thumbs up/down.

---

### Scale milestones

| Traffic | What breaks first | Fix |
|---|---|---|
| ~10 concurrent users | Ollama queue depth | Cloud LLM or GPU |
| ~100 req/s | SQLite write lock | Postgres + Redis |
| ~1,000 req/s | Single API instance | Horizontal scale + load balancer |
| Multi-tenant / B2B | Shared KB, no auth | Per-org KB namespaces, JWT, RBAC |
| Real personalisation | 6-message memory limit | User profiles + wearable context via `UserContextProvider` |

---

### What doesn't change

The `LLMAdapter` ABC, the stateless agent loop, and the `UserContextProvider` seam mean most upgrades above are **additive** — you swap an implementation class or add a new one. The agent orchestration in `finn.py`, the guardrails classifier, the RAG retriever, and the prompt builder stay the same across all scale tiers.

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
