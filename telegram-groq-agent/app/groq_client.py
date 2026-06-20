"""Groq chat client with proactive key scheduling and provider failover."""

import re
import time
from typing import Any

import httpx


RETRYABLE_KEY_STATUS_CODES = {401, 403, 429, 500, 502, 503, 504}


class GroqAPIError(RuntimeError):
    """Error returned by the Groq API."""

    def __init__(self, status_code: int, message: str, headers: httpx.Headers | None = None):
        super().__init__(f"Groq API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.headers = headers or httpx.Headers()


class GroqClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "llama-3.1-8b-instant",
        api_keys: list[str] | None = None,
        min_remaining_requests: int = 3,
        min_remaining_tokens: int = 1500,
    ):
        keys = api_keys or ([api_key] if api_key else [])

        # Remove empty values and duplicate keys while keeping the same order.
        self.api_keys = list(dict.fromkeys(key for key in keys if key))
        if not self.api_keys:
            raise ValueError("Missing GROQ_API_KEY or GROQ_API_KEYS")

        self.model = model
        # These reserves make the client leave a key before its limit reaches zero.
        self.min_remaining_requests = max(0, min_remaining_requests)
        self.min_remaining_tokens = max(0, min_remaining_tokens)
        self.active_key_index = 0
        self.last_key_index: int | None = None
        self.key_status: dict[int, dict[str, Any]] = {}
        self.cooldown_until: dict[int, float] = {}

    async def chat(self, messages: list[dict[str, str]], *, max_tokens: int = 450) -> str:
        """Ask Groq for a normal text answer."""
        payload = self._payload(messages=messages, max_tokens=max_tokens)
        data = await self._post(payload)
        return data["choices"][0]["message"]["content"].strip()

    async def chat_json(self, messages: list[dict[str, str]], *, max_tokens: int = 900) -> str:
        """Ask Groq for a structured JSON answer."""
        payload = self._payload(messages=messages, max_tokens=max_tokens)
        payload["response_format"] = {"type": "json_object"}
        data = await self._post(payload)
        return data["choices"][0]["message"]["content"].strip()

    def _payload(self, messages: list[dict[str, str]], *, max_tokens: int) -> dict:
        return {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }

    async def _post(self, payload: dict) -> dict:
        """Use a healthy key and move away from keys close to their limits."""
        failures: list[str] = []

        candidate_indexes = self._candidate_indexes()
        if not candidate_indexes:
            raise RuntimeError("All Groq keys are cooling down; trying the fallback provider")

        for index in candidate_indexes:
            api_key = self.api_keys[index]
            try:
                data, headers = await self._post_once(payload, api_key)
                self.last_key_index = index
                self._record_success(index, headers)
                return data
            except GroqAPIError as exc:
                rate_details = self._rate_headers(exc.headers)
                self.key_status[index] = {
                    "state": f"error {exc.status_code}",
                    "message": exc.message,
                    **rate_details,
                }
                failures.append(f"key {index + 1}: {exc.status_code} {exc.message}")

                # A rate-limited key rests until Groq says its quota resets.
                if exc.status_code == 429:
                    self._start_cooldown(index, exc.headers, "rate limited")

                if exc.status_code not in RETRYABLE_KEY_STATUS_CODES:
                    raise
            except httpx.RequestError as exc:
                self.key_status[index] = {"state": "network error", "message": str(exc)}
                failures.append(f"key {index + 1}: network error")

        raise RuntimeError("All Groq keys failed: " + "; ".join(failures))

    async def _post_once(self, payload: dict, api_key: str) -> tuple[dict, httpx.Headers]:
        """Send one request using one Groq key."""
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code >= 400:
            try:
                error_message = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                error_message = response.text
            raise GroqAPIError(response.status_code, error_message, response.headers)

        return response.json(), response.headers

    def _rate_headers(self, headers: httpx.Headers) -> dict[str, str]:
        """Extract quota details without storing any secret key."""
        return {
            "request_limit": headers.get("x-ratelimit-limit-requests", "unknown"),
            "requests_remaining": headers.get("x-ratelimit-remaining-requests", "unknown"),
            "request_reset": headers.get("x-ratelimit-reset-requests", "unknown"),
            "token_limit": headers.get("x-ratelimit-limit-tokens", "unknown"),
            "tokens_remaining": headers.get("x-ratelimit-remaining-tokens", "unknown"),
            "token_reset": headers.get("x-ratelimit-reset-tokens", "unknown"),
        }

    def _candidate_indexes(self) -> list[int]:
        """Return ready keys, beginning with the current active key."""
        now = time.monotonic()
        ready: list[int] = []

        for offset in range(len(self.api_keys)):
            index = (self.active_key_index + offset) % len(self.api_keys)
            cooldown_end = self.cooldown_until.get(index, 0)
            if cooldown_end <= now:
                self.cooldown_until.pop(index, None)
                ready.append(index)

        return ready

    def _record_success(self, index: int, headers: httpx.Headers) -> None:
        """Store limits and proactively rest a key when its reserve is low."""
        rate_details = self._rate_headers(headers)
        low_reasons: list[str] = []

        requests_remaining = self._to_int(rate_details["requests_remaining"])
        tokens_remaining = self._to_int(rate_details["tokens_remaining"])

        if requests_remaining is not None and requests_remaining <= self.min_remaining_requests:
            low_reasons.append("request reserve low")
        if tokens_remaining is not None and tokens_remaining <= self.min_remaining_tokens:
            low_reasons.append("token reserve low")

        self.key_status[index] = {"state": "working", **rate_details}

        if low_reasons and len(self.api_keys) > 1:
            self._start_cooldown(index, headers, ", ".join(low_reasons))
            self.active_key_index = (index + 1) % len(self.api_keys)
        else:
            self.active_key_index = index

    def _start_cooldown(self, index: int, headers: httpx.Headers, reason: str) -> None:
        """Keep a low key out of rotation until its relevant quota resets."""
        rate_details = self._rate_headers(headers)
        durations: list[float] = []

        # Retry-After is normally seconds. Groq reset headers may look like 7.5s or 2m30s.
        retry_after = headers.get("retry-after")
        if retry_after:
            try:
                durations.append(float(retry_after))
            except ValueError:
                pass

        if "request" in reason or reason == "rate limited":
            durations.append(self._parse_duration(rate_details["request_reset"]))
        if "token" in reason or reason == "rate limited":
            durations.append(self._parse_duration(rate_details["token_reset"]))

        cooldown_seconds = max((value for value in durations if value > 0), default=60.0)
        self.cooldown_until[index] = time.monotonic() + cooldown_seconds
        self.key_status[index] = {
            "state": f"cooling down: {reason}",
            "cooldown_seconds": cooldown_seconds,
            **rate_details,
        }

    @staticmethod
    def _to_int(value: str) -> int | None:
        """Convert a quota header to an integer when Groq supplied one."""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_duration(value: str) -> float:
        """Convert values such as 1h2m3.5s or 250ms into seconds."""
        if not value or value == "unknown":
            return 0.0

        total = 0.0
        units = {"h": 3600.0, "m": 60.0, "s": 1.0, "ms": 0.001}
        for amount, unit in re.findall(r"([0-9]*\.?[0-9]+)(ms|h|m|s)", value.lower()):
            total += float(amount) * units[unit]
        return total

    def rate_limit_summary(self) -> str:
        """Show non-secret status and quota information for each configured key."""
        lines = [f"Configured Groq keys: {len(self.api_keys)}"]

        for index in range(len(self.api_keys)):
            status = self.key_status.get(index)
            if not status:
                lines.append(f"Key {index + 1}: not tried yet")
                continue

            active = " (active)" if index == self.active_key_index else ""
            lines.append(f"Key {index + 1}: {status['state']}{active}")
            if status.get("requests_remaining"):
                lines.append(
                    f"  Requests: {status['requests_remaining']} / {status['request_limit']} "
                    f"(reset {status['request_reset']})"
                )
                lines.append(
                    f"  Tokens this minute: {status['tokens_remaining']} / {status['token_limit']} "
                    f"(reset {status['token_reset']})"
                )

        return "\n".join(lines)
