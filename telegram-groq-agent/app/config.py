"""Loads settings for the bot from the local .env file.

This file is the central place where the app reads private keys, model name,
clinic knowledge path, and local data folder path.
"""

from pathlib import Path
import os

from dotenv import load_dotenv


# BASE_DIR points to the main telegram-groq-agent folder.
BASE_DIR = Path(__file__).resolve().parents[1]

# This reads variables from telegram-groq-agent/.env.
load_dotenv(BASE_DIR / ".env")


def resolve_from_base(value: str) -> Path:
    """Turn a relative path from .env into a full absolute path.

    Example:
    ../royce-aesthetics-agent becomes D:/Business Agent/royce-aesthetics-agent.
    """
    path = Path(value)
    if path.is_absolute():
        return path
    return (BASE_DIR / path).resolve()


def positive_int_setting(name: str, default: int) -> int:
    """Read a non-negative whole number from .env, or use a safe default."""
    try:
        return max(0, int(os.getenv(name, str(default))))
    except ValueError:
        return default


# Token for your Telegram bot.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

# API key used to talk to Groq.
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# Optional list of Groq keys, separated by commas in .env.
GROQ_API_KEYS = [
    key.strip()
    for key in os.getenv("GROQ_API_KEYS", GROQ_API_KEY).split(",")
    if key.strip()
]

# Groq model name. The default is a fast, cheap/free-friendly model.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()

# Move to another Groq key before the active key reaches zero.
GROQ_MIN_REMAINING_REQUESTS = positive_int_setting("GROQ_MIN_REMAINING_REQUESTS", 3)
GROQ_MIN_REMAINING_TOKENS = positive_int_setting("GROQ_MIN_REMAINING_TOKENS", 1500)

# Gemini is used as a separate-provider fallback when Groq is unavailable.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip()

# Folder where the clinic knowledge files live.
BUSINESS_PACK_DIR = resolve_from_base(os.getenv("BUSINESS_PACK_DIR", "../royce-aesthetics-agent"))

# Folder where chats, sessions, and leads are saved.
DATA_DIR = resolve_from_base(os.getenv("DATA_DIR", "./data"))

# Optional Telegram chat ID where staff alerts are sent.
STAFF_ALERT_CHAT_ID = os.getenv("STAFF_ALERT_CHAT_ID", "").strip()
