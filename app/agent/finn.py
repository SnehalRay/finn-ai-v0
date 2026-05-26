import uuid
from dataclasses import dataclass

from app.agent.greeter import check_greeting
from app.agent.guardrails import classify, GuardrailResult
from app.agent.prompts import build_system_prompt
from app.db import database as db
from app.db.models import Role
from app.llm.base import LLMAdapter
from app.privacy.sanitizer import sanitize_pii
from app.rag.retriever import retrieve_context
from app.config import settings


@dataclass
class AgentResponse:
    session_id: str
    text: str
    blocked: bool
    block_reason: str | None  # CRISIS | MEDICAL | OTHER, or None if not blocked
    sources_used: bool        # True if RAG context was injected


class FinnAgent:
    def __init__(self, llm: LLMAdapter):
        self.llm = llm

    async def chat(
        self,
        user_message: str,
        user_id: str,
        session_id: str | None = None,
    ) -> AgentResponse:
        # 1. Resolve session — create if new
        if not session_id:
            session_id = str(uuid.uuid4())
        db.create_session(session_id, user_id)

        # 2. Sanitize PII before any persistence or processing
        clean_message = sanitize_pii(user_message)

        # 3. Save user message
        db.save_message(session_id, Role.user, clean_message)

        # 4. Social check (greetings + farewells + fillers) — runs before guardrails
        greeting = await check_greeting(clean_message, self.llm)
        if greeting.is_social:
            db.save_message(session_id, Role.assistant, greeting.response)
            return AgentResponse(
                session_id=session_id,
                text=greeting.response,
                blocked=False,
                block_reason=None,
                sources_used=False,
            )

        # 5. Guardrails — LLM classifier with short history for follow-up context
        guard_history = db.get_session_messages(session_id, limit=4)
        guard: GuardrailResult = await classify(clean_message, self.llm, history=guard_history)
        if guard.should_block:
            db.save_message(session_id, Role.assistant, guard.response)
            return AgentResponse(
                session_id=session_id,
                text=guard.response,
                blocked=True,
                block_reason=guard.category,
                sources_used=False,
            )

        # 6. RAG retrieval
        context = retrieve_context(clean_message)

        # 7. Load conversation history window
        history = db.get_session_messages(session_id, limit=settings.MAX_CONTEXT_MESSAGES)

        # 8. Build system prompt (with or without RAG context)
        system = build_system_prompt(context)

        # 9. LLM call
        reply = await self.llm.complete(system=system, messages=history)

        # 10. Persist assistant reply
        db.save_message(session_id, Role.assistant, reply)

        return AgentResponse(
            session_id=session_id,
            text=reply,
            blocked=False,
            block_reason=None,
            sources_used=bool(context),
        )
