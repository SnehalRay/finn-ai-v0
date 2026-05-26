from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.agent.finn import FinnAgent
from app.api.middleware import add_middleware
from app.api.routes import chat, health
from app.llm.ollama_adapter import get_llm_adapter
from app.rag.embedder import get_embedder
from app.rag.vector_store import get_vector_store

# Module-level — populated during lifespan startup, used by route dependency
finn_agent: FinnAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global finn_agent

    # Initialise all singletons once at startup (not per-request)
    print("[startup] Loading embedding model...")
    get_embedder()

    print("[startup] Connecting to ChromaDB...")
    get_vector_store()

    print("[startup] Initialising Ollama adapter...")
    llm = get_llm_adapter()

    print("[startup] Finn is ready.")
    finn_agent = FinnAgent(llm=llm)

    yield

    print("[shutdown] Finn shutting down.")


app = FastAPI(
    title="Finn — fini AI Wellness Bot",
    description="Ask Finn anything about nutrition, sleep, hydration, exercise, or mental wellbeing.",
    version="0.1.0",
    lifespan=lifespan,
)

add_middleware(app)

app.include_router(health.router, tags=["System"])
app.include_router(chat.router, tags=["Chat"])
