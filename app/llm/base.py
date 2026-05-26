from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """
    Abstract base for LLM backends. Swap providers by implementing this interface.
    Current implementation: OllamaAdapter (local, free).
    Future: ClaudeAdapter, OpenAIAdapter, etc.
    """

    @abstractmethod
    async def complete(
        self,
        system: str,
        messages: list[dict],
        max_tokens: int = 512,
    ) -> str:
        """
        Send a chat completion request.

        Args:
            system:     System prompt (Finn's persona + RAG context).
            messages:   Conversation history as [{"role": "user"|"assistant", "content": str}].
            max_tokens: Soft cap on response length.

        Returns:
            The assistant's reply as a plain string.
        """
        ...
