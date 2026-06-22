"""Helpers for local WhatsApp testing without Meta Cloud API credentials."""

from __future__ import annotations

from typing import Any


class SimulationWhatsAppClient:
    """Captures outbound WhatsApp replies instead of calling Meta Graph API."""

    def __init__(self) -> None:
        self.replies: dict[str, list[str]] = {}

    async def send_text(self, to: str, text: str) -> None:
        self.replies.setdefault(to, []).append(text)

    def pop_replies(self, phone: str) -> list[str]:
        return self.replies.pop(phone, [])

    def last_reply(self, phone: str) -> str | None:
        messages = self.replies.get(phone) or []
        return messages[-1] if messages else None


def build_meta_webhook_payload(from_phone: str, body: str) -> dict[str, Any]:
    """Build a Meta WhatsApp webhook JSON body for one inbound text message."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "SIMULATED_ENTRY",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550001111",
                                "phone_number_id": "SIMULATED",
                            },
                            "contacts": [
                                {
                                    "profile": {"name": "Test User"},
                                    "wa_id": from_phone,
                                }
                            ],
                            "messages": [
                                {
                                    "from": from_phone,
                                    "id": "wamid.SIMULATED",
                                    "timestamp": "1719000000",
                                    "type": "text",
                                    "text": {"body": body},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


DEFAULT_SCENARIOS: list[tuple[str, str]] = [
    ("Clinic kahan hai phase 7 mein?", "Location FAQ — Roman Urdu"),
    ("Underarms laser kitni hai?", "Laser pricing"),
    ("Mujhe appointment book karni hai acne ke liye", "Booking intent"),
    ("Tell me a joke", "Off-topic redirect"),
    ("My face is swollen and burning after a cream", "Urgent escalation"),
]
