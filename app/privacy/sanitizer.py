import re

# Patterns applied to every user message before storage or embedding.
# The vector store and SQLite never see raw PII.
_PII_PATTERNS = [
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]"),                          # US phone
    (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL]"),             # email
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),                                         # SSN
    (r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b", "[CARD]"),             # credit card
]


def sanitize_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text
