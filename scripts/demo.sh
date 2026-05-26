#!/bin/bash
# Finn AI — quick demo
# Sends three representative messages and prints the responses.
# Usage: bash scripts/demo.sh
# The backend must already be running (http://localhost:8000).

set -e

BASE="http://localhost:8000"
BOLD=$(tput bold 2>/dev/null || true)
RESET=$(tput sgr0 2>/dev/null || true)

# -- Wait for server ----------------------------------------------------------

echo "Waiting for backend..."
until curl -sf "$BASE/health" > /dev/null; do
    sleep 1
done
echo "Backend ready."
echo ""

# -- Helper -------------------------------------------------------------------

send() {
    local label="$1"
    local payload="$2"
    echo "${BOLD}--- $label ---${RESET}"
    echo "Request: $payload"
    echo ""
    curl -sf -X POST "$BASE/chat" \
        -H "Content-Type: application/json" \
        -d "$payload" | python3 -m json.tool
    echo ""
}

# -- Demo 1: In-scope wellness question (RAG grounded) ------------------------

SESSION=$(python3 -c "import uuid; print(uuid.uuid4())")

send "In-scope: hydration question" \
    "{\"user_id\": \"demo\", \"session_id\": \"$SESSION\", \"message\": \"How much water should I drink daily?\"}"

# -- Demo 2: Follow-up in same session (tests conversation memory) ------------

send "Follow-up in same session" \
    "{\"user_id\": \"demo\", \"session_id\": \"$SESSION\", \"message\": \"What are signs that I am dehydrated?\"}"

# -- Demo 3: Crisis message (guardrails — fixed hotline response) -------------

send "Crisis: guardrails block" \
    "{\"user_id\": \"demo\", \"message\": \"I want to hurt myself\"}"

# -- Demo 4: Out-of-scope (dynamic redirect/decline) -------------------------

send "Out-of-scope: finance question" \
    "{\"user_id\": \"demo\", \"message\": \"What stocks should I buy right now?\"}"
