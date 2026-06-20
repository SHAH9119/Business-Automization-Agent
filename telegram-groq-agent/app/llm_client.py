"""Provider router: Groq first, Gemini second."""

import logging

from app.gemini_client import GeminiClient
from app.groq_client import GroqClient


logger = logging.getLogger(__name__)


class FallbackLLMClient:
    def __init__(self, groq: GroqClient, gemini: GeminiClient | None = None):
        self.groq = groq
        self.gemini = gemini
        self.last_provider = "none"
        self.last_groq_error = ""

    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int = 450) -> str:
        return await self._call("chat", messages, max_tokens=max_tokens)

    async def chat_json(self, messages: list[dict[str, str]], *, max_tokens: int = 900) -> str:
        return await self._call("chat_json", messages, max_tokens=max_tokens)

    async def _call(self, method: str, messages: list[dict[str, str]], *, max_tokens: int) -> str:
        try:
            result = await getattr(self.groq, method)(messages, max_tokens=max_tokens)
            self.last_provider = "groq"
            return result
        except Exception as exc:
            self.last_groq_error = str(exc)
            logger.warning("Groq unavailable; trying Gemini fallback")

        if not self.gemini:
            raise RuntimeError(self.last_groq_error)

        result = await getattr(self.gemini, method)(messages, max_tokens=max_tokens)
        self.last_provider = "gemini"
        return result

    def rate_limit_summary(self) -> str:
        """Status for the hidden /limits admin command."""
        sections = [f"Last provider used: {self.last_provider}", self.groq.rate_limit_summary()]
        if self.gemini:
            sections.append(self.gemini.status_summary())
        return "\n\n".join(sections)
