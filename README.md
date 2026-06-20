# Business Automization Agent

Low-cost AI receptionist prototype for service businesses. The current demo
connects Telegram to Groq with Gemini fallback, answers clinic questions from a
structured catalog, collects appointment requests, alerts staff, rotates API
providers safely, and blocks common spam and prompt-injection attempts.

## Projects

- `telegram-groq-agent/`: Python Telegram receptionist application and tests.
- `royce-aesthetics-agent/`: Demo clinic knowledge, service catalog, prices,
  conversation examples, and operating flows.

## Run The Bot

See `telegram-groq-agent/README.md` for setup and operating instructions. Copy
the provided `.env.example` to `.env` and supply your own private API keys.

Private keys, customer conversations, leads, and calendar credentials are
excluded from Git by the repository `.gitignore`.
