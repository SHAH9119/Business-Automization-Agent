# Telegram + Groq Clinic Agent

Low-cost first MVP for testing the WhatsApp/SMS agent flow.

This version uses Telegram as the test channel, Groq as the primary LLM, and Gemini as an optional fallback. Later, the `telegram_bot.py` adapter can be replaced with a WhatsApp Cloud API adapter while keeping the same agent logic.

## What It Does

- Reads the Royce Aesthetics demo knowledge pack.
- Replies as a clinic receptionist.
- Collects appointment request details.
- Tracks name, phone, concern, preferred day, and preferred time.
- Saves conversations, sessions, and leads locally under `data/`.
- Sends a staff-style summary when enough details are collected.
- Supports `/start`, `/help`, `/status`, `/reset`, and `/id`.
- Supports hidden `/limits` for provider/key status and Groq quota headers.
- Proactively rests a Groq key near its request/token limit and uses the next ready key.
- Blocks message floods, repeated spam, oversized input, obvious gibberish, and common prompt-injection attempts before calling the AI.
- Avoids diagnosis, prescriptions, and treatment guarantees.

## What You Need

- Telegram bot token from BotFather.
- One or more Groq API keys.
- Optional Gemini API key for separate-provider fallback.

## Setup

Fast setup:

```powershell
.\scripts\setup_env.ps1
.\scripts\run_bot.ps1
```

Manual setup:

1. Copy `.env.example` to `.env`.
2. Fill in:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
GROQ_API_KEYS=key_one,key_two
GROQ_MIN_REMAINING_REQUESTS=3
GROQ_MIN_REMAINING_TOKENS=1500
GROQ_MODEL=llama-3.1-8b-instant
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash
BUSINESS_PACK_DIR=../royce-aesthetics-agent
DATA_DIR=./data
STAFF_ALERT_CHAT_ID=
```

3. Install dependencies:

```powershell
pip install -r requirements.txt
```

4. Run the bot:

```powershell
python -m app.telegram_bot
```

Or:

```powershell
.\scripts\run_bot.ps1
```

## Telegram Token

In Telegram:

1. Open `@BotFather`.
2. Send `/newbot`.
3. Choose a bot name and username.
4. Copy the token into `.env`.

## Staff Alerts

To receive staff alerts in Telegram:

1. Run the bot.
2. Send `/id` to the bot from your own Telegram account.
3. Copy the returned chat ID into `STAFF_ALERT_CHAT_ID` in `.env`.
4. Restart the bot.

## How This Becomes WhatsApp Later

The important logic lives in `app/agent.py`.

Telegram-specific code lives in `app/telegram_bot.py`.

Later, you can add a WhatsApp Cloud API adapter that sends incoming WhatsApp messages to the same `ReceptionistAgent.reply(...)` method.

```text
Telegram now:
Telegram -> telegram_bot.py -> ReceptionistAgent -> Groq/Gemini -> Telegram

WhatsApp later:
Meta WhatsApp -> whatsapp_webhook.py -> ReceptionistAgent -> Groq/Gemini -> Meta WhatsApp
```

## Security

- Never commit `.env`.
- Rotate keys if they were shared publicly.
- Keep one client/business per config at first.
- Do not use this as a medical advice bot.
- Do not claim this is an official clinic assistant without permission.
- Add client separation before serving multiple real businesses.

## Tests

```powershell
.\scripts\test.ps1
```

## Notes

This is a private demo. Do not present it as an official Royce Aesthetics assistant unless the clinic authorizes it.
