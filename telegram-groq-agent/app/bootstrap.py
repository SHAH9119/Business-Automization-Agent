"""Shared wiring for Telegram, WhatsApp, and future channels."""

from __future__ import annotations

from app.agent import ReceptionistAgent
from app.business_config import BusinessConfig
from app.config import (
    BUSINESS_PACK_DIR,
    DATA_DIR,
    EMAIL_FROM_NAME,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GMAIL_APP_PASSWORD,
    GMAIL_SMTP_USER,
    GROQ_API_KEYS,
    GROQ_MIN_REMAINING_REQUESTS,
    GROQ_MIN_REMAINING_TOKENS,
    GROQ_MODEL,
    N8N_WEBHOOK_URL,
    STAFF_EMAIL,
)
from app.email_notifier import EmailNotifier
from app.gemini_client import GeminiClient
from app.groq_client import GroqClient
from app.integrations import WebhookNotifier
from app.knowledge import load_section_retriever, load_service_catalog
from app.llm_client import FallbackLLMClient
from app.storage import JsonStorage


def load_business_config() -> BusinessConfig:
    return BusinessConfig.from_pack_dir(BUSINESS_PACK_DIR)


def create_webhook_notifier() -> WebhookNotifier | None:
    notifier = WebhookNotifier(N8N_WEBHOOK_URL)
    return notifier if notifier.enabled else None


def create_email_notifier() -> EmailNotifier | None:
    notifier = EmailNotifier(
        smtp_user=GMAIL_SMTP_USER,
        smtp_app_password=GMAIL_APP_PASSWORD,
        staff_email=STAFF_EMAIL,
        from_name=EMAIL_FROM_NAME,
    )
    return notifier if notifier.enabled else None


def create_receptionist_agent(
    *,
    business_config: BusinessConfig | None = None,
    webhook_notifier: WebhookNotifier | None = None,
    email_notifier: EmailNotifier | None = None,
) -> ReceptionistAgent:
    """Build the channel-agnostic receptionist agent."""
    config = business_config or load_business_config()
    knowledge = load_section_retriever(BUSINESS_PACK_DIR)
    service_catalog = load_service_catalog(BUSINESS_PACK_DIR)
    storage = JsonStorage(DATA_DIR)

    groq = GroqClient(
        api_keys=GROQ_API_KEYS,
        model=GROQ_MODEL,
        min_remaining_requests=GROQ_MIN_REMAINING_REQUESTS,
        min_remaining_tokens=GROQ_MIN_REMAINING_TOKENS,
    )
    gemini = GeminiClient(api_key=GEMINI_API_KEY, model=GEMINI_MODEL) if GEMINI_API_KEY else None
    llm = FallbackLLMClient(groq=groq, gemini=gemini)

    return ReceptionistAgent(
        groq=llm,
        storage=storage,
        business_knowledge=knowledge,
        service_catalog=service_catalog,
        business_config=config,
        webhook_notifier=webhook_notifier,
        email_notifier=email_notifier,
    )
