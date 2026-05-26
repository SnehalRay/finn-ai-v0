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
GREETING — purely opening the conversation, no personal info or wellness content.
Examples:
  "hi" → GREETING
  "hello" → GREETING
  "hey there" → GREETING
  "good morning" → GREETING
  "who are you?" → GREETING
  "what can you help with?" → GREETING

---
FAREWELL — ONLY these: a pure sign-off or a standalone one/two-word positive reaction
with absolutely no personal information, emotion, or wellness content.
Examples:
  "bye" → FAREWELL
  "thanks" → FAREWELL
  "ok thanks" → FAREWELL
  "cool" → FAREWELL
  "got it" → FAREWELL
  "perfect" → FAREWELL
  "noted" → FAREWELL
  "sounds good" → FAREWELL
  "see ya" → FAREWELL

NOT farewell — send these to CONTINUE:
  "I am doing good" → CONTINUE  (personal update about how they feel)
  "im good" → CONTINUE  (personal state, even without apostrophe)
  "i'm fine" → CONTINUE  (personal state)
  "not bad" → CONTINUE  (personal state)
  "my mind is foggy" → CONTINUE  (personal wellness complaint)
  "huh" → CONTINUE  (confusion — needs engagement)
  "what?" → CONTINUE  (confusion — needs engagement)
  "yeah" → CONTINUE  (conversational affirmation — continues the dialogue)
  "yep" → CONTINUE  (conversational affirmation)
  "yup" → CONTINUE  (conversational affirmation)
  "nah" → CONTINUE  (conversational negation — continues the dialogue)
  "nope" → CONTINUE  (conversational negation)
  "I feel tired" → CONTINUE  (personal feeling)
  "not great" → CONTINUE  (personal state)
  "ok but what about sleep?" → CONTINUE  (has new content)

---
CONTINUE — everything else. When in doubt, always choose CONTINUE.
This includes:
  - Any message that mentions how someone feels or their personal state
  - Any wellness question or topic
  - Any expression of confusion ("huh?", "what?", "I don't understand")
  - Any message with emotional content, even if short
  - Anything ambiguous

---
Critical rule: If the message contains ANY personal information, emotion, or body/mind state,
it is ALWAYS CONTINUE — even if it's short or positive ("I am doing good", "feeling fine").

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
# Affirmations/negations always continue the conversation — never sign-offs
_CONTINUE_TOKENS = {"yeah", "yep", "yup", "nah", "nope", "yes", "no", "sure", "maybe"}


async def check_greeting(message: str, llm: LLMAdapter) -> GreetingResult:
    normalised = message.strip().lower().rstrip("!.,?")

    # Fast path — unambiguous short tokens, no LLM call needed
    if normalised in _GREETING_TOKENS:
        return GreetingResult(category="GREETING", is_social=True, response=_GREETING_RESPONSE)
    if normalised in _FAREWELL_TOKENS:
        return GreetingResult(category="FAREWELL", is_social=True, response=_FAREWELL_RESPONSE)
    if normalised in _CONTINUE_TOKENS:
        return GreetingResult(category="CONTINUE", is_social=False, response=None)

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
