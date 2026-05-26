"""
Greeting classifier — runs before the main guardrails classifier.

Detects when a user is saying hello, introducing themselves, or asking what
Finn can do. Returns a warm intro response instead of sending the message
through the full RAG + LLM pipeline.
"""

from dataclasses import dataclass
from app.llm.base import LLMAdapter


_SOCIAL_CLASSIFIER_SYSTEM = """You are a classifier for a wellness chatbot called Finn.

Classify the user's message into one of three categories: GREETING, FAREWELL, or CONTINUE.

---
GREETING — opening the conversation or asking about Finn. No wellness content yet.
Examples:
  "hi" → GREETING
  "hello there" → GREETING
  "hey, what's up?" → GREETING
  "who are you?" → GREETING
  "what can you help me with?" → GREETING
  "good morning!" → GREETING

---
FAREWELL — wrapping up, acknowledging, or reacting with no new question.
This includes short positive reactions, confirmations, and sign-offs.
Examples:
  "bye" → FAREWELL
  "thanks" → FAREWELL
  "ok" → FAREWELL
  "cool" → FAREWELL
  "perfect" → FAREWELL
  "alright" → FAREWELL
  "got it" → FAREWELL
  "i see" → FAREWELL
  "alright i see" → FAREWELL
  "that makes sense" → FAREWELL
  "good to know" → FAREWELL
  "that helps, thanks" → FAREWELL
  "makes sense!" → FAREWELL
  "awesome" → FAREWELL
  "noted" → FAREWELL
  "sounds good" → FAREWELL
  "ok thank you" → FAREWELL
  "see you later" → FAREWELL

---
CONTINUE — the message contains actual content that needs a response.
Examples:
  "how much water should I drink?" → CONTINUE
  "I've been feeling really anxious lately" → CONTINUE
  "what foods give me energy?" → CONTINUE
  "I can't sleep" → CONTINUE
  "I was diagnosed with anxiety" → CONTINUE
  "perfect, now tell me about sleep" → CONTINUE  ← has a follow-up question
  "ok but what about exercise?" → CONTINUE  ← has new content after the filler

---
Key rule: if the message is ONLY a reaction/filler with no new question or topic, it is FAREWELL.
If it contains a question or new topic (even after a filler word), it is CONTINUE.

Reply with ONLY one word: GREETING, FAREWELL, or CONTINUE."""


_GREETING_RESPONSE = """\
Hey there! I'm **Finn** 👋 — your personal wellness companion built into fini.

I'm here to help you with all things health and wellness:
- 🥗 **Nutrition** — eating habits, macros, energy foods
- 💧 **Hydration** — how much water, signs of dehydration
- 😴 **Sleep** — sleep hygiene, how much you need
- 🏃 **Exercise** — getting started, building habits
- 🧘 **Mental wellbeing** — stress, anxiety, mood, breathing techniques

What's on your mind today?"""

_FAREWELL_RESPONSE = """\
Take care! 😊 Remember — small consistent habits make the biggest difference. Come back anytime you need a wellness check-in. I'm always here."""


@dataclass
class GreetingResult:
    category: str        # GREETING | FAREWELL | CONTINUE
    is_social: bool      # True if GREETING or FAREWELL (skip main pipeline)
    response: str | None # pre-written response if social, None if CONTINUE


# Minimal fast-path — only crystal-clear single tokens where an LLM call is wasteful.
# Everything else goes through the LLM classifier.
_FAREWELL_TOKENS = {"bye", "goodbye", "cya", "later", "thanks", "thx", "ty", "got it", "gotcha"}
_GREETING_TOKENS = {"hi", "hey", "hello", "howdy", "hiya"}


async def check_greeting(message: str, llm: LLMAdapter) -> GreetingResult:
    normalised = message.strip().lower().rstrip("!.,?")

    # Fast path — unambiguous short tokens, no LLM call needed
    if normalised in _GREETING_TOKENS:
        return GreetingResult(category="GREETING", is_social=True, response=_GREETING_RESPONSE)
    if normalised in _FAREWELL_TOKENS:
        return GreetingResult(category="FAREWELL", is_social=True, response=_FAREWELL_RESPONSE)

    # LLM classifier for longer / ambiguous messages
    raw = await llm.complete(
        system=_SOCIAL_CLASSIFIER_SYSTEM,
        messages=[{"role": "user", "content": message}],
        max_tokens=5,
    )

    word = raw.strip().upper().split()[0] if raw.strip() else "CONTINUE"
    if word not in {"GREETING", "FAREWELL", "CONTINUE"}:
        word = "CONTINUE"

    responses = {
        "GREETING": _GREETING_RESPONSE,
        "FAREWELL": _FAREWELL_RESPONSE,
    }

    return GreetingResult(
        category=word,
        is_social=word in {"GREETING", "FAREWELL"},
        response=responses.get(word),
    )
