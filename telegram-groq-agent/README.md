# Business Agent — Telegram & WhatsApp Clinic Bot

Multi-channel AI receptionist for aesthetic clinics and other businesses. Same agent core, swappable business pack.

## Channels

| Channel | Status | Run command |
|---|---|---|
| **Telegram** | ✅ Polling (free demo) | `.\scripts\run_bot.ps1` |
| **WhatsApp** | ✅ Cloud API webhook | `.\scripts\run_whatsapp.ps1` |
| SMS / Voice | Planned | Same `ReceptionistAgent` |

## What It Does

- Loads tenant settings from `agent_config.json` (greetings, hours, phone, escalation keywords)
- Reads business knowledge from a swappable pack (`BUSINESS_PACK_DIR`)
- Replies as a clinic receptionist in **English** or **Roman Urdu**
- Collects appointment requests and saves leads locally
- Sends staff alerts via **Telegram** and/or **WhatsApp**
- POSTs lead events to **n8n** for email, Google Calendar, Sheets automation
- Groq multi-key rotation + optional Gemini fallback
- Spam/injection protection before LLM calls

## Quick Start — Telegram

```powershell
.\scripts\setup_env.ps1
# Edit .env with TELEGRAM_BOT_TOKEN and GROQ_API_KEY
.\scripts\run_bot.ps1
```

## Quick Start — WhatsApp

1. Get Meta WhatsApp Cloud API credentials (see `docs/whatsapp-setup.md`)
2. Add to `.env`:

```env
WHATSAPP_ACCESS_TOKEN=your_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=business-agent-verify
```

3. Run webhook server and expose with ngrok:

```powershell
pip install -r requirements.txt
.\scripts\run_whatsapp.ps1
# In another terminal: ngrok http 8000
```

4. Register `https://your-ngrok-url/webhook` in Meta Developer Console

Full guide: **[docs/whatsapp-setup.md](docs/whatsapp-setup.md)**

### Local testing (no Meta account)

```powershell
# Terminal 1 — simulation server (no WhatsApp API keys needed)
.\scripts\run_whatsapp_simulation.ps1

# Terminal 2 — send fake WhatsApp messages
python scripts/simulate_whatsapp.py --mode http --message "Clinic kahan hai?"
python scripts/simulate_whatsapp.py --mode http --scenarios
python scripts/simulate_whatsapp.py --mode direct --booking
```

Set `WHATSAPP_SIMULATION_MODE=true` in `.env` or use `run_whatsapp_simulation.ps1`.

## Gmail Appointment Alerts (Recommended — No n8n)

Free email to your inbox when a customer books. See **[docs/gmail-setup.md](docs/gmail-setup.md)**.

```env
GMAIL_SMTP_USER=your@gmail.com
GMAIL_APP_PASSWORD=your-google-app-password
STAFF_EMAIL=your@gmail.com
```

```powershell
python scripts/test_email.py
```

## n8n Automation (Optional)

```powershell
docker compose up -d   # starts n8n on http://localhost:5678
```

Create a webhook workflow, then set in `.env`:

```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/clinic-lead
```

Full guide: **[docs/n8n-setup.md](docs/n8n-setup.md)** (includes: should you use n8n? Docker vs alternatives)

Test webhook without a real booking:

```powershell
python scripts/test_n8n_webhook.py
```

## Environment Variables

See `.env.example` for all options. Key ones:

| Variable | Purpose |
|---|---|
| `BUSINESS_PACK_DIR` | Path to clinic knowledge pack |
| `GROQ_API_KEYS` | Comma-separated Groq keys for rotation |
| `N8N_WEBHOOK_URL` | Optional n8n webhook (Calendar/Sheets — skip if using Gmail only) |
| `GMAIL_SMTP_USER` | Gmail account that sends appointment emails |
| `GMAIL_APP_PASSWORD` | Google App Password (16 chars) |
| `STAFF_EMAIL` | Inbox that receives appointment alerts |
| `WHATSAPP_ACCESS_TOKEN` | Meta WhatsApp API token |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta phone number ID |
| `STAFF_ALERT_CHAT_ID` | Telegram chat for staff alerts |
| `WHATSAPP_STAFF_PHONE` | Staff WhatsApp for lead alerts |

## Architecture

```text
Telegram ──→ telegram_bot.py ──┐
                                ├──→ ReceptionistAgent ──→ Groq/Gemini
WhatsApp ──→ whatsapp_webhook.py ┘           │
                                              ├──→ Local JSON leads
                                              ├──→ Staff alert (TG/WA)
                                              └──→ n8n webhook → Email/Calendar/Sheet
```

## Customize for Another Business

1. Copy `../royce-aesthetics-agent/` to a new folder
2. Edit `config/agent_config.json` and `knowledge/*.md`
3. Set `BUSINESS_PACK_DIR` in `.env`
4. No code changes required

## Tests

```powershell
.\scripts\test.ps1
```

## Security

- Never commit `.env`
- Use HTTPS for WhatsApp webhooks in production
- Do not present as official clinic assistant without permission
- Agent does not diagnose or prescribe

## Docs

- [WhatsApp setup](docs/whatsapp-setup.md)
- [n8n automation](docs/n8n-setup.md)
- [Deployment & cloud guide](docs/deployment.md)
- [Gmail alerts setup](docs/gmail-setup.md)
- [Royce Aesthetics knowledge pack](../royce-aesthetics-agent/README.md)
