from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.agent.finn import FinnAgent, AgentResponse
from app.db import database as db


router = APIRouter()


# ---------- request / response models ----------

class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    session_id: str | None = Field(default=None)
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    session_id: str
    message: str
    blocked: bool
    block_reason: str | None
    sources_used: bool


class MessageDTO(BaseModel):
    role: str
    content: str
    created_at: float


class HistoryResponse(BaseModel):
    session_id: str
    messages: list[MessageDTO]


# ---------- dependency ----------

def get_agent() -> FinnAgent:
    # Imported lazily so the singleton is resolved after lifespan initialises it
    from app.main import finn_agent
    return finn_agent


# ---------- routes ----------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, agent: FinnAgent = Depends(get_agent)):
    result: AgentResponse = await agent.chat(
        user_message=req.message,
        user_id=req.user_id,
        session_id=req.session_id,
    )
    return ChatResponse(
        session_id=result.session_id,
        message=result.text,
        blocked=result.blocked,
        block_reason=result.block_reason,
        sources_used=result.sources_used,
    )


@router.get("/chat/history/{session_id}", response_model=HistoryResponse)
async def history(session_id: str):
    messages = db.get_all_messages(session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Session not found")
    return HistoryResponse(
        session_id=session_id,
        messages=[MessageDTO(**m) for m in messages],
    )
