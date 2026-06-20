"""Gemini API client used as a separate-provider fallback."""

from typing import Any

import httpx


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY")
        self.api_key = api_key
        self.model = model
        self.last_status = "not tried yet"
        self.last_usage: dict[str, Any] = {}

    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int = 450) -> str:
        """Ask Gemini for a normal text response."""
        return await self._generate(messages, max_tokens=max_tokens, json_mode=False)

    async def chat_json(self, messages: list[dict[str, str]], *, max_tokens: int = 900) -> str:
        """Ask Gemini for a JSON response."""
        return await self._generate(messages, max_tokens=max_tokens, json_mode=True)

    async def _generate(self, messages: list[dict[str, str]], *, max_tokens: int, json_mode: bool) -> str:
        system_text, contents = self._convert_messages(messages)
        generation_config: dict[str, Any] = {
            "temperature": 0.2,
            # Newer Gemini models may use part of this budget for thinking.
            "maxOutputTokens": max(max_tokens, 2048),
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config,
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                url,
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            try:
                message = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                message = response.text
            self.last_status = f"error {response.status_code}: {message}"
            raise RuntimeError(f"Gemini API error {response.status_code}: {message}")

        self.last_status = "working"
        data = response.json()
        self.last_usage = data.get("usageMetadata") or {}
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no response candidate")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text

    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[str, list[dict[str, Any]]]:
        """Convert OpenAI/Groq-style messages into Gemini's request format."""
        system_parts: list[str] = []
        contents: list[dict[str, Any]] = []

        for message in messages:
            role = message.get("role", "user")
            text = message.get("content", "")
            if role == "system":
                system_parts.append(text)
                continue

            gemini_role = "model" if role == "assistant" else "user"
            contents.append({"role": gemini_role, "parts": [{"text": text}]})

        if not contents:
            contents.append({"role": "user", "parts": [{"text": "Please respond."}]})

        return "\n\n".join(system_parts), contents

    def status_summary(self) -> str:
        """Return provider status without exposing the API key."""
        total_tokens = self.last_usage.get("totalTokenCount", "unknown")
        return (
            f"Gemini model: {self.model}\n"
            f"Gemini status: {self.last_status}\n"
            f"Tokens used in latest Gemini request: {total_tokens}"
        )
