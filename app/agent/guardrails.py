"""
Guardrails — LLM-based message classifier.

Every user message is classified before reaching the main agent loop.
The LLM is given nuanced examples so it can distinguish context:
  - "I was diagnosed with anxiety" → WELLNESS  (sharing a story, engage)
  - "Do I have diabetes?"          → MEDICAL   (asking Finn to diagnose)
  - "I feel really hopeless"       → WELLNESS  (emotional, engage with care)
  - "I want to hurt myself"        → CRISIS    (active intent, redirect immediately)
  - "What stocks should I buy?"    → OTHER     (out of scope)
"""

from dataclasses import dataclass
from app.llm.base import LLMAdapter


_CLASSIFIER_SYSTEM = """You are a content safety classifier for Finn, an AI wellness chatbot.

Your job is to classify a user's message into EXACTLY ONE of these four categories:

WELLNESS  — anything related to general health, fitness, nutrition, hydration, sleep,
            mental wellbeing, emotions, or lifestyle. This includes:
            • Conversational follow-ups and clarification requests — ALWAYS classify these as WELLNESS,
              even if the words have no health content on their own:
              "clarify?", "explain more", "tell me more", "can you elaborate?",
              "what do you mean?", "more details?", "go on", "why?", "how so?", "and?"
            • Sharing personal health stories ("I was diagnosed with X", "I've been feeling X")
            • Asking general wellness questions ("how much water should I drink?")
            • Expressing emotions like sadness, stress, or anxiety in a general way
            • Mentioning medications or conditions as context in a story (not asking for advice)

MEDICAL   — the user is explicitly asking Finn to diagnose a condition, recommend a
            specific medication or dosage, or provide clinical treatment advice. Examples:
            • "Do I have diabetes?"
            • "What medication should I take for my headaches?"
            • "Can you tell me if these symptoms mean I have X?"
            • "Should I stop taking my prescription?"

CRISIS    — the user is expressing active intent or immediate desire to harm themselves
            or others. This is NOT triggered by general sadness or hopelessness alone.
            Only classify as CRISIS if there is clear, present-tense intent. Examples:
            • "I want to kill myself"
            • "I'm thinking about ending my life tonight"
            • "I want to hurt someone"
            NOT crisis: "I feel hopeless", "life feels hard", "I've struggled with dark thoughts in the past"

OTHER     — the message is completely unrelated to health or wellness. Examples:
            • Finance, investing, crypto
            • Legal advice
            • Recipes or restaurant recommendations
            • Politics, sports, entertainment

Reply with ONLY one word: WELLNESS, MEDICAL, CRISIS, or OTHER.
Do not explain. Do not punctuate. Just the single word."""


_GUARDRAIL_RESPONSES: dict[str, str] = {
    "CRISIS": (
        "It sounds like you're going through something really painful right now, "
        "and I want you to know that support is available.\n\n"
        "Please reach out to someone who can help:\n"
        "• **988 Suicide & Crisis Lifeline** — call or text 988 (US)\n"
        "• **Crisis Text Line** — text HOME to 741741\n"
        "• **International Association for Suicide Prevention** — https://www.iasp.info/resources/Crisis_Centres/\n\n"
        "You don't have to face this alone. 💙"
    ),
    "MEDICAL": (
        "That's a great question to bring up, but it's outside what I'm able to help with safely. "
        "Diagnosing conditions or recommending specific treatments really needs a licensed healthcare provider "
        "who knows your full history.\n\n"
        "What I *can* do is share general wellness information — things like nutrition, sleep, "
        "stress management, and staying active. Is there something in those areas I can help with?"
    ),
}

_OTHER_SYSTEM = """You are Finn, a friendly AI wellness companion. A user has just asked you something outside your area of expertise.

Your job is to respond in one of three ways — pick whichever fits best:

1. REDIRECT — if their question has a wellness angle, acknowledge it and pivot to that angle.
   Example: "best pasta recipe?" → mention nutrition instead of the recipe itself.

2. CLARIFY — if the question is ambiguous and could have a wellness interpretation, ask a short clarifying question.
   Example: "help with my routine" → ask if they mean a fitness or wellness routine.

3. POLITELY DECLINE — if it's completely unrelated (finance, sports, coding, politics, etc.), briefly acknowledge, say you specialise in wellness, and offer to help with one of: nutrition, hydration, sleep, exercise, or mental wellbeing.

Rules:
- Keep it warm, never dismissive or robotic.
- Maximum 3 sentences.
- Always end with an offer or question to keep the conversation going.
- Never say "I cannot" or "I am not able to" — say what you CAN do instead."""


@dataclass
class GuardrailResult:
    category: str        # WELLNESS | MEDICAL | CRISIS | OTHER
    should_block: bool
    response: str | None # pre-written response if blocked, None if WELLNESS


async def classify(message: str, llm: LLMAdapter) -> GuardrailResult:
    """Run the LLM classifier on a user message and return a GuardrailResult."""
    raw = await llm.complete(
        system=_CLASSIFIER_SYSTEM,
        messages=[{"role": "user", "content": message}],
        max_tokens=5,
    )

    category = raw.strip().upper().split()[0] if raw.strip() else "OTHER"
    if category not in {"WELLNESS", "MEDICAL", "CRISIS", "OTHER"}:
        category = "WELLNESS"

    should_block = category != "WELLNESS"

    if not should_block:
        return GuardrailResult(category=category, should_block=False, response=None)

    # CRISIS and MEDICAL use fixed responses; OTHER gets a dynamic contextual one
    if category in _GUARDRAIL_RESPONSES:
        response = _GUARDRAIL_RESPONSES[category]
    else:
        response = await llm.complete(
            system=_OTHER_SYSTEM,
            messages=[{"role": "user", "content": message}],
            max_tokens=128,
        )

    return GuardrailResult(category=category, should_block=True, response=response)
