"""Tests for n8n webhook integration."""

import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.integrations import WebhookNotifier


class WebhookNotifierTest(unittest.TestCase):
    def test_disabled_when_url_empty(self):
        notifier = WebhookNotifier("")
        self.assertFalse(notifier.enabled)

    def test_notify_lead_posts_payload(self):
        notifier = WebhookNotifier("https://example.com/hook")

        mock_response = AsyncMock()
        mock_response.raise_for_status = lambda: None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("app.integrations.httpx.AsyncClient", return_value=mock_client):
            result = asyncio.run(
                notifier.notify_lead(
                    event="lead_saved",
                    channel="whatsapp",
                    chat_id="wa:923001234567",
                    business_name="Test Clinic",
                    tenant_id="test",
                    status="appointment_request",
                    profile={"name": "Ali"},
                    staff_summary="summary",
                )
            )

        self.assertTrue(result)
        mock_client.post.assert_awaited_once()
        payload = mock_client.post.await_args.kwargs["json"]
        self.assertEqual(payload["channel"], "whatsapp")
        self.assertEqual(payload["profile"]["name"], "Ali")
