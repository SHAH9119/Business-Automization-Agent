"""Tests for Groq key recovery and Gemini provider fallback."""

import asyncio
import unittest

import httpx

from app.groq_client import GroqAPIError, GroqClient
from app.llm_client import FallbackLLMClient


class FakeProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = 0

    async def chat(self, messages, *, max_tokens=450):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result

    async def chat_json(self, messages, *, max_tokens=900):
        return await self.chat(messages, max_tokens=max_tokens)

    def rate_limit_summary(self):
        return "fake limits"

    def status_summary(self):
        return "fake fallback status"


class ProviderFallbackTest(unittest.TestCase):
    def test_uses_gemini_when_groq_fails(self):
        primary = FakeProvider(error=RuntimeError("Groq unavailable"))
        fallback = FakeProvider(result="Gemini reply")
        client = FallbackLLMClient(primary, fallback)

        result = asyncio.run(client.chat([{"role": "user", "content": "Hello"}]))

        self.assertEqual(result, "Gemini reply")
        self.assertEqual(client.last_provider, "gemini")
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 1)

    def test_does_not_call_gemini_when_groq_works(self):
        primary = FakeProvider(result="Groq reply")
        fallback = FakeProvider(result="Gemini reply")
        client = FallbackLLMClient(primary, fallback)

        result = asyncio.run(client.chat([{"role": "user", "content": "Hello"}]))

        self.assertEqual(result, "Groq reply")
        self.assertEqual(client.last_provider, "groq")
        self.assertEqual(fallback.calls, 0)


class GroqKeyRecoveryTest(unittest.TestCase):
    def test_tries_next_key_after_authentication_failure(self):
        client = GroqClient(api_keys=["key-one", "key-two"])
        attempted = []

        async def fake_post_once(payload, api_key):
            attempted.append(api_key)
            if api_key == "key-one":
                raise GroqAPIError(401, "invalid key")
            return (
                {"choices": [{"message": {"content": "OK"}}]},
                httpx.Headers({"x-ratelimit-remaining-requests": "99"}),
            )

        client._post_once = fake_post_once
        result = asyncio.run(client.chat([{"role": "user", "content": "Hello"}]))

        self.assertEqual(result, "OK")
        self.assertEqual(attempted, ["key-one", "key-two"])
        self.assertEqual(client.last_key_index, 1)

    def test_rotates_keys_on_rate_limit(self):
        client = GroqClient(api_keys=["key-one", "key-two"])
        attempted = []

        async def fake_post_once(payload, api_key):
            attempted.append(api_key)
            if api_key == "key-one":
                raise GroqAPIError(
                    429,
                    "rate limited",
                    httpx.Headers({"x-ratelimit-reset-tokens": "10s"}),
                )
            return (
                {"choices": [{"message": {"content": "OK"}}]},
                httpx.Headers({"x-ratelimit-remaining-requests": "99"}),
            )

        client._post_once = fake_post_once
        result = asyncio.run(client.chat([{"role": "user", "content": "Hello"}]))

        self.assertEqual(result, "OK")
        self.assertEqual(attempted, ["key-one", "key-two"])
        self.assertIn(0, client.cooldown_until)

    def test_proactively_uses_next_key_when_request_reserve_is_low(self):
        client = GroqClient(
            api_keys=["key-one", "key-two"],
            min_remaining_requests=3,
        )
        attempted = []

        async def fake_post_once(payload, api_key):
            attempted.append(api_key)
            remaining = "3" if api_key == "key-one" else "99"
            return (
                {"choices": [{"message": {"content": "OK"}}]},
                httpx.Headers(
                    {
                        "x-ratelimit-remaining-requests": remaining,
                        "x-ratelimit-reset-requests": "1h",
                    }
                ),
            )

        client._post_once = fake_post_once
        messages = [{"role": "user", "content": "Hello"}]
        asyncio.run(client.chat(messages))
        asyncio.run(client.chat(messages))

        self.assertEqual(attempted, ["key-one", "key-two"])
        self.assertIn("request reserve low", client.key_status[0]["state"])

    def test_proactively_uses_next_key_when_token_reserve_is_low(self):
        client = GroqClient(
            api_keys=["key-one", "key-two"],
            min_remaining_tokens=1500,
        )
        attempted = []

        async def fake_post_once(payload, api_key):
            attempted.append(api_key)
            remaining = "1200" if api_key == "key-one" else "5000"
            return (
                {"choices": [{"message": {"content": "OK"}}]},
                httpx.Headers(
                    {
                        "x-ratelimit-remaining-tokens": remaining,
                        "x-ratelimit-reset-tokens": "5s",
                    }
                ),
            )

        client._post_once = fake_post_once
        messages = [{"role": "user", "content": "Hello"}]
        asyncio.run(client.chat(messages))
        asyncio.run(client.chat(messages))

        self.assertEqual(attempted, ["key-one", "key-two"])
        self.assertIn("token reserve low", client.key_status[0]["state"])

    def test_duration_parser_handles_groq_reset_format(self):
        self.assertEqual(GroqClient._parse_duration("1h2m3.5s"), 3723.5)
        self.assertEqual(GroqClient._parse_duration("250ms"), 0.25)


if __name__ == "__main__":
    unittest.main()
