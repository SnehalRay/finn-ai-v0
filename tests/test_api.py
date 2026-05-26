import pytest
from fastapi.testclient import TestClient

from tests.conftest import MockLLMAdapter


# ---------- health ----------

def test_health(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------- POST /chat — happy path ----------

def test_chat_returns_session_id(api_client):
    resp = api_client.post("/chat", json={"user_id": "u1", "message": "how much water?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID4


def test_chat_wellness_not_blocked(api_client):
    resp = api_client.post("/chat", json={"user_id": "u2", "message": "how do I sleep better?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["blocked"] is False
    assert data["block_reason"] is None


def test_chat_session_is_reused(api_client):
    first = api_client.post("/chat", json={"user_id": "u3", "message": "hello"}).json()
    sid = first["session_id"]
    second = api_client.post("/chat", json={"user_id": "u3", "session_id": sid, "message": "how are you?"}).json()
    assert second["session_id"] == sid


# ---------- POST /chat — guardrail blocks ----------

def test_chat_crisis_is_blocked(api_client):
    from app.agent.finn import FinnAgent
    from app.api.routes.chat import get_agent
    from app.main import app

    agent = FinnAgent(llm=MockLLMAdapter(response="CRISIS"))
    app.dependency_overrides[get_agent] = lambda: agent

    resp = api_client.post("/chat", json={"user_id": "u_crisis", "message": "I want to hurt myself"})
    data = resp.json()
    assert data["blocked"] is True
    assert data["block_reason"] == "CRISIS"
    assert "988" in data["message"]

    app.dependency_overrides.clear()


def test_chat_medical_is_blocked(api_client):
    from app.agent.finn import FinnAgent
    from app.api.routes.chat import get_agent
    from app.main import app

    agent = FinnAgent(llm=MockLLMAdapter(response="MEDICAL"))
    app.dependency_overrides[get_agent] = lambda: agent

    resp = api_client.post("/chat", json={"user_id": "u_med", "message": "do I have diabetes?"})
    data = resp.json()
    assert data["blocked"] is True
    assert data["block_reason"] == "MEDICAL"

    app.dependency_overrides.clear()


# ---------- POST /chat — validation ----------

def test_chat_empty_message_rejected(api_client):
    resp = api_client.post("/chat", json={"user_id": "u4", "message": ""})
    assert resp.status_code == 422


def test_chat_missing_user_id_rejected(api_client):
    resp = api_client.post("/chat", json={"message": "hello"})
    assert resp.status_code == 422


# ---------- GET /chat/history ----------

def test_history_returns_messages(api_client):
    chat_resp = api_client.post("/chat", json={"user_id": "u5", "message": "how much protein?"}).json()
    sid = chat_resp["session_id"]
    hist = api_client.get(f"/chat/history/{sid}").json()
    assert hist["session_id"] == sid
    assert len(hist["messages"]) == 2  # user + assistant
    assert hist["messages"][0]["role"] == "user"
    assert hist["messages"][1]["role"] == "assistant"


def test_history_unknown_session_returns_404(api_client):
    resp = api_client.get("/chat/history/nonexistent-session-id")
    assert resp.status_code == 404
