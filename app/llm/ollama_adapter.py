import httpx
from app.llm.base import LLMAdapter
from app.config import settings

_TIMEOUT = httpx.Timeout(120.0, connect=5.0)

_OFFLINE_MSG = (
    "I'm having a little trouble thinking right now — please try again in a moment. "
    "If this keeps happening, make sure Ollama is running (`ollama serve`)."
)


class OllamaAdapter(LLMAdapter):
    def __init__(self, base_url: str | None = None, model: str | None = None):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL

    async def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 512,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": "system", "content": system}, *messages],
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"].strip()

        except (httpx.ConnectError, httpx.ConnectTimeout):
            return _OFFLINE_MSG
        except httpx.HTTPStatusError as e:
            return f"The AI backend returned an error ({e.response.status_code}). Please try again."
        except Exception:
            return _OFFLINE_MSG


_adapter: OllamaAdapter | None = None


def get_llm_adapter() -> OllamaAdapter:
    global _adapter
    if _adapter is None:
        _adapter = OllamaAdapter()
    return _adapter
