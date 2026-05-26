import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.llm.base import LLMAdapter


class MockLLMAdapter(LLMAdapter):
    """Returns a fixed response — keeps tests fast and deterministic."""

    def __init__(self, response: str = "WELLNESS"):
        self._response = response

    async def complete(self, system: str, messages: list[dict], max_tokens: int = 512) -> str:
        return self._response


@pytest.fixture
def mock_llm():
    return MockLLMAdapter(response="WELLNESS")


@pytest.fixture
def wellness_llm():
    return MockLLMAdapter(response="WELLNESS")


@pytest.fixture
def crisis_llm():
    return MockLLMAdapter(response="CRISIS")


@pytest.fixture
def medical_llm():
    return MockLLMAdapter(response="MEDICAL")


@pytest.fixture
def other_llm():
    return MockLLMAdapter(response="OTHER")


@pytest.fixture
def api_client(mock_llm):
    """TestClient with a mocked FinnAgent — no real Ollama needed."""
    from app.agent.finn import FinnAgent
    from app.api.routes.chat import get_agent
    from app.main import app

    agent = FinnAgent(llm=mock_llm)

    app.dependency_overrides[get_agent] = lambda: agent
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
