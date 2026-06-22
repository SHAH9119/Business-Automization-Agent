"""Outbound integrations — n8n webhooks, email/calendar automation hooks."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WebhookNotifier:
    """POST lead events to an n8n (or any) webhook URL."""

    def __init__(self, webhook_url: str, *, timeout_seconds: float = 8.0):
        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = timeout_seconds

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    async def notify_lead(
        self,
        *,
        event: str,
        channel: str,
        chat_id: str,
        business_name: str,
        tenant_id: str,
        status: str,
        profile: dict[str, Any],
        staff_summary: str | None = None,
        handoff_reason: str | None = None,
        lead_file: str | None = None,
    ) -> bool:
        """Fire-and-forget webhook call. Returns True on HTTP 2xx."""
        if not self.enabled:
            return False

        payload = {
            "event": event,
            "channel": channel,
            "chat_id": chat_id,
            "business_name": business_name,
            "tenant_id": tenant_id,
            "status": status,
            "profile": profile,
            "staff_summary": staff_summary,
            "handoff_reason": handoff_reason,
            "lead_file": lead_file,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
            logger.info("Webhook delivered: %s (%s)", event, status)
            return True
        except Exception as exc:
            logger.warning("Webhook delivery failed: %s", exc)
            return False
