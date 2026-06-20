"""Telegram channel adapter.

This file connects Telegram to our receptionist agent.

Telegram message -> this file -> ReceptionistAgent -> Groq -> this file -> Telegram reply
"""

import asyncio
import logging

import httpx

from app.agent import ReceptionistAgent
from app.config import (
    BUSINESS_PACK_DIR,
    DATA_DIR,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEYS,
    GROQ_MIN_REMAINING_REQUESTS,
    GROQ_MIN_REMAINING_TOKENS,
    GROQ_MODEL,
    STAFF_ALERT_CHAT_ID,
    TELEGRAM_BOT_TOKEN,
)
from app.gemini_client import GeminiClient
from app.groq_client import GroqClient
from app.knowledge import load_business_knowledge, load_service_catalog
from app.llm_client import FallbackLLMClient
from app.message_guard import MessageGuard
from app.storage import JsonStorage


# Basic logging so we can see when the bot receives messages or errors.
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# httpx logs full request URLs. Telegram puts the private bot token in its URL,
# so keep httpx/httpcore logs at WARNING to prevent the token appearing in terminal logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class TelegramBot:
    def __init__(self, token: str, agent: ReceptionistAgent, message_guard: MessageGuard | None = None):
        # The Telegram bot token is required to call Telegram's Bot API.
        if not token:
            raise ValueError("Missing TELEGRAM_BOT_TOKEN")
        self.token = token
        self.agent = agent

        # The guard stops spam and obvious attacks before they consume AI quota.
        self.message_guard = message_guard or MessageGuard()

        # Base URL for all Telegram Bot API requests.
        self.base_url = f"https://api.telegram.org/bot{token}"

        # offset tells Telegram which updates we already processed.
        self.offset = 0

    async def run_polling(self) -> None:
        """Keep asking Telegram for new messages forever."""
        logger.info("Telegram bot polling started")
        async with httpx.AsyncClient(timeout=40) as client:
            # Make sure polling works even if a webhook was set before.
            await self._delete_webhook(client)

            while True:
                # Get new Telegram messages.
                updates = await self._get_updates(client)
                for update in updates:
                    # Mark this update as processed.
                    self.offset = update["update_id"] + 1
                    await self._handle_update(client, update)

                # Small pause so we do not hammer Telegram's API.
                await asyncio.sleep(0.5)

    async def _get_updates(self, client: httpx.AsyncClient) -> list[dict]:
        """Ask Telegram for new incoming messages."""
        response = await client.get(
            f"{self.base_url}/getUpdates",
            params={"offset": self.offset, "timeout": 25, "allowed_updates": ["message"]},
        )
        response.raise_for_status()
        return response.json().get("result", [])

    async def _handle_update(self, client: httpx.AsyncClient, update: dict) -> None:
        """Handle one Telegram update/message."""
        message = update.get("message") or {}
        chat = message.get("chat") or {}
        text = message.get("text", "").strip()
        chat_id = str(chat.get("id", ""))

        # Ignore non-text messages for now.
        if not chat_id or not text:
            return

        logger.info("Message from %s", chat_id)

        # Commands like /start and /reset are handled before the AI agent.
        command_reply = self._handle_command(chat_id, text)
        if command_reply:
            await self._send_message(client, chat_id, command_reply)
            return

        # Security and spam checks happen before saving or sending text to the AI.
        guard_decision = self.message_guard.check(chat_id, text)
        if not guard_decision.allowed:
            logger.warning("Blocked message from %s: %s", chat_id, guard_decision.reason)
            if guard_decision.reply:
                await self._send_message(client, chat_id, guard_decision.reply)
            return

        try:
            # Send user text to the receptionist brain.
            reply, staff_summary = await self.agent.reply(chat_id, text)
        except Exception as exc:
            # If anything breaks, do not expose technical errors to the user.
            logger.exception("Agent error")
            reply = "Sorry, something went wrong in the demo assistant. Please try again."
            staff_summary = f"Agent error for chat {chat_id}: {exc}"

        # Reply to the user.
        await self._send_message(client, chat_id, reply)

        # Optional: send staff/admin summary if STAFF_ALERT_CHAT_ID is configured.
        if staff_summary and STAFF_ALERT_CHAT_ID:
            await self._send_message(client, STAFF_ALERT_CHAT_ID, staff_summary)

    def _handle_command(self, chat_id: str, text: str) -> str | None:
        """Handle simple Telegram commands without using AI."""
        command = text.split()[0].lower().split("@")[0]

        if command == "/start":
            return (
                "Hello! This is a demo AI receptionist for Royce Aesthetics.\n\n"
                "I can help with general service information and appointment requests. "
                "How may I help you today?"
            )

        if command == "/help":
            return (
                "I can help with clinic services, timings, location, and appointment requests. "
                "Please type your question or tell me which service you are interested in."
            )

        if command == "/reset":
            self.agent.reset(chat_id)
            return "Done. I cleared this test conversation."

        if command == "/status":
            return self.agent.status_summary(chat_id)

        if command == "/id":
            return f"Your Telegram chat ID is: {chat_id}"

        if command == "/limits":
            return self.agent.groq.rate_limit_summary()

        return None

    async def _delete_webhook(self, client: httpx.AsyncClient) -> None:
        """Disable Telegram webhook mode so polling can work."""
        response = await client.post(f"{self.base_url}/deleteWebhook", json={"drop_pending_updates": False})
        response.raise_for_status()

    async def _send_message(self, client: httpx.AsyncClient, chat_id: str, text: str) -> None:
        """Send a message back to a Telegram chat."""
        response = await client.post(
            f"{self.base_url}/sendMessage",
            # Telegram message limit is around 4096 chars, so we keep it under that.
            json={"chat_id": chat_id, "text": text[:3900]},
        )
        response.raise_for_status()


async def main() -> None:
    """Create all app parts and start the bot."""
    # Load clinic knowledge from markdown files.
    knowledge = load_business_knowledge(BUSINESS_PACK_DIR)

    # Load structured services and demo prices for reliable factual answers.
    service_catalog = load_service_catalog(BUSINESS_PACK_DIR)

    # Create local JSON storage.
    storage = JsonStorage(DATA_DIR)

    # Create Groq primary provider with controlled key failover.
    groq = GroqClient(
        api_keys=GROQ_API_KEYS,
        model=GROQ_MODEL,
        min_remaining_requests=GROQ_MIN_REMAINING_REQUESTS,
        min_remaining_tokens=GROQ_MIN_REMAINING_TOKENS,
    )

    # Create Gemini as a separate-provider fallback when configured.
    gemini = GeminiClient(api_key=GEMINI_API_KEY, model=GEMINI_MODEL) if GEMINI_API_KEY else None
    llm = FallbackLLMClient(groq=groq, gemini=gemini)

    # Create receptionist agent.
    agent = ReceptionistAgent(
        groq=llm,
        storage=storage,
        business_knowledge=knowledge,
        service_catalog=service_catalog,
    )

    # Create Telegram adapter and start listening.
    bot = TelegramBot(token=TELEGRAM_BOT_TOKEN, agent=agent)
    await bot.run_polling()


if __name__ == "__main__":
    # Runs main() when you execute: python -m app.telegram_bot
    asyncio.run(main())
