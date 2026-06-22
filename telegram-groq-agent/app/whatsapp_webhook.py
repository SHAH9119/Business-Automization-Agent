"""WhatsApp Cloud API channel adapter.

Receives Meta webhook events and routes them to the same ReceptionistAgent used by Telegram.

Setup:
1. Create a Meta app with WhatsApp product.
2. Get a permanent access token and phone number ID.
3. Set webhook URL to https://your-domain/webhook (use ngrok for local testing).
4. Fill WHATSAPP_* variables in .env and run: python -m app.whatsapp_webhook
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import FastAPI, Query, Request, Response

from app.bootstrap import create_email_notifier, create_receptionist_agent, create_webhook_notifier, load_business_config
from app.config import (
    STAFF_ALERT_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
    WEBHOOK_HOST,
    WEBHOOK_PORT,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_API_VERSION,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_SIMULATION_MODE,
    WHATSAPP_STAFF_PHONE,
    WHATSAPP_VERIFY_TOKEN,
)
from app.message_guard import MessageGuard
from app.whatsapp_simulation import SimulationWhatsAppClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

business_config = load_business_config()
agent = create_receptionist_agent(
    business_config=business_config,
    webhook_notifier=create_webhook_notifier(),
    email_notifier=create_email_notifier(),
)
agent.channel = "whatsapp"

message_guard = MessageGuard()
app = FastAPI(title="Business Agent WhatsApp Webhook", version="1.0.0")
_whatsapp_client: WhatsAppClient | SimulationWhatsAppClient | None = None
simulation_client = SimulationWhatsAppClient()


def get_whatsapp_client() -> WhatsAppClient | SimulationWhatsAppClient:
    global _whatsapp_client
    if _whatsapp_client is None:
        if WHATSAPP_SIMULATION_MODE:
            _whatsapp_client = simulation_client
        else:
            _whatsapp_client = WhatsAppClient(
                WHATSAPP_ACCESS_TOKEN,
                WHATSAPP_PHONE_NUMBER_ID,
                WHATSAPP_API_VERSION,
            )
    return _whatsapp_client


class WhatsAppClient:
    """Minimal Meta Graph API client for sending WhatsApp text messages."""

    def __init__(self, access_token: str, phone_number_id: str, api_version: str = "v21.0"):
        if not access_token or not phone_number_id:
            raise ValueError("Missing WHATSAPP_ACCESS_TOKEN or WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    async def send_text(self, to: str, text: str) -> None:
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text[:3900]},
        }
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()


async def send_staff_alert(summary: str) -> None:
    """Deliver staff alerts via WhatsApp staff number and/or Telegram."""
    if WHATSAPP_STAFF_PHONE:
        try:
            await get_whatsapp_client().send_text(WHATSAPP_STAFF_PHONE, summary)
        except Exception:
            logger.exception("Failed to send WhatsApp staff alert")

    if STAFF_ALERT_CHAT_ID and TELEGRAM_BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            async with httpx.AsyncClient(timeout=20) as client:
                await client.post(
                    url,
                    json={"chat_id": STAFF_ALERT_CHAT_ID, "text": summary[:3900]},
                )
        except Exception:
            logger.exception("Failed to send Telegram staff alert")


def extract_text_messages(payload: dict[str, Any]) -> list[tuple[str, str]]:
    """Return (sender_phone, message_text) pairs from a Meta webhook payload."""
    messages: list[tuple[str, str]] = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            for message in value.get("messages", []):
                if message.get("type") != "text":
                    continue
                sender = str(message.get("from", "")).strip()
                body = ((message.get("text") or {}).get("body") or "").strip()
                if sender and body:
                    messages.append((sender, body))
    return messages


@app.get("/")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "channel": "whatsapp",
        "business": business_config.business_name,
        "simulation_mode": str(WHATSAPP_SIMULATION_MODE).lower(),
    }


@app.get("/webhook")
async def verify_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> Response:
    """Meta webhook verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return Response(content=hub_challenge or "", media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


def _capture_simulated_replies(sender: str, captured: dict[str, list[str]]) -> None:
    if not WHATSAPP_SIMULATION_MODE:
        return
    client = get_whatsapp_client()
    if isinstance(client, SimulationWhatsAppClient):
        replies = client.pop_replies(sender)
    else:
        replies = simulation_client.pop_replies(sender)
    if replies:
        captured[sender] = replies


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, Any]:
    """Handle incoming WhatsApp messages."""
    payload = await request.json()
    captured_replies: dict[str, list[str]] = {}

    for sender, text in extract_text_messages(payload):
        chat_id = f"wa:{sender}"
        logger.info("WhatsApp message from %s", sender)

        lowered = text.strip().lower()
        if lowered in {"/start", "start", "hi", "hello", "salam", "assalamu alaikum"}:
            reply = business_config.greeting(
                roman_urdu=any(word in lowered for word in {"salam", "assalam", "alaikum"})
            )
            await get_whatsapp_client().send_text(sender, reply)
            _capture_simulated_replies(sender, captured_replies)
            continue

        if lowered in {"/help", "help"}:
            await get_whatsapp_client().send_text(sender, business_config.help_en)
            _capture_simulated_replies(sender, captured_replies)
            continue

        if lowered == "/reset":
            agent.reset(chat_id)
            await get_whatsapp_client().send_text(sender, "Done. I cleared this conversation.")
            _capture_simulated_replies(sender, captured_replies)
            continue

        guard_decision = message_guard.check(chat_id, text)
        if not guard_decision.allowed:
            logger.warning("Blocked WhatsApp message from %s: %s", sender, guard_decision.reason)
            if guard_decision.reply:
                await get_whatsapp_client().send_text(sender, guard_decision.reply)
            _capture_simulated_replies(sender, captured_replies)
            continue

        try:
            reply, staff_summary = await agent.reply(chat_id, text)
        except Exception as exc:
            logger.exception("Agent error for WhatsApp chat %s", sender)
            reply = "Sorry, something went wrong. Please try again or call the clinic directly."
            staff_summary = f"Agent error for WhatsApp {sender}: {exc}"

        await get_whatsapp_client().send_text(sender, reply)
        if staff_summary:
            await send_staff_alert(staff_summary)

        _capture_simulated_replies(sender, captured_replies)

    response: dict[str, Any] = {"status": "ok"}
    if WHATSAPP_SIMULATION_MODE and captured_replies:
        response["simulated_replies"] = captured_replies
    return response


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.whatsapp_webhook:app",
        host=WEBHOOK_HOST,
        port=WEBHOOK_PORT,
        reload=False,
    )


if __name__ == "__main__":
    main()
