"""Tests for WhatsApp simulation helpers and HTTP webhook with simulation mode."""

import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.whatsapp_simulation import DEFAULT_SCENARIOS, SimulationWhatsAppClient, build_meta_webhook_payload


class WhatsAppSimulationTest(unittest.TestCase):
    def test_build_meta_webhook_payload(self):
        payload = build_meta_webhook_payload("923001234567", "Hello")
        messages = payload["entry"][0]["changes"][0]["value"]["messages"]
        self.assertEqual(messages[0]["from"], "923001234567")
        self.assertEqual(messages[0]["text"]["body"], "Hello")

    def test_simulation_client_captures_replies(self):
        client = SimulationWhatsAppClient()

        async def run():
            await client.send_text("923001234567", "Reply one")
            await client.send_text("923001234567", "Reply two")

        import asyncio

        asyncio.run(run())
        self.assertEqual(client.pop_replies("923001234567"), ["Reply one", "Reply two"])

    def test_default_scenarios_not_empty(self):
        self.assertGreaterEqual(len(DEFAULT_SCENARIOS), 4)


class WhatsAppWebhookHttpTest(unittest.TestCase):
    def test_webhook_returns_simulated_replies(self):
        with patch("app.whatsapp_webhook.WHATSAPP_SIMULATION_MODE", True):
            with patch("app.whatsapp_webhook._whatsapp_client", None):
                with patch("app.whatsapp_webhook.get_whatsapp_client") as mock_get:
                    sim = SimulationWhatsAppClient()
                    mock_get.return_value = sim

                    with patch.object(
                        __import__("app.whatsapp_webhook", fromlist=["agent"]).agent,
                        "reply",
                        new=AsyncMock(return_value=("Test agent reply", None)),
                    ):
                        from app.whatsapp_webhook import app

                        client = TestClient(app)
                        payload = build_meta_webhook_payload("923001234567", "What are your hours?")
                        response = client.post("/webhook", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("923001234567", body.get("simulated_replies", {}))
        self.assertIn("Test agent reply", body["simulated_replies"]["923001234567"][-1])

    def test_greeting_simulation_without_agent(self):
        with patch("app.whatsapp_webhook.WHATSAPP_SIMULATION_MODE", True):
            with patch("app.whatsapp_webhook._whatsapp_client", None):
                with patch("app.whatsapp_webhook.get_whatsapp_client") as mock_get:
                    sim = SimulationWhatsAppClient()
                    mock_get.return_value = sim

                    from app.whatsapp_webhook import app

                    client = TestClient(app)
                    payload = build_meta_webhook_payload("923001234567", "Salam")
                    response = client.post("/webhook", json=payload)

        self.assertEqual(response.status_code, 200)
        replies = response.json().get("simulated_replies", {}).get("923001234567", [])
        self.assertTrue(replies)
        self.assertIn("khush aamdeed", replies[-1].lower())

    def test_webhook_verify_handshake(self):
        from app.whatsapp_webhook import app

        client = TestClient(app)
        response = client.get(
            "/webhook",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "business-agent-verify",
                "hub.challenge": "challenge-abc",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "challenge-abc")
