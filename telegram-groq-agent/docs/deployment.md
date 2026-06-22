# Deployment Guide — Cloud, Local LLM, No n8n

## Do you need to deploy?

| Use case | Deploy? | Where |
|---|---|---|
| **Telegram demo on your laptop** | No | Run locally while PC is on |
| **WhatsApp for a real clinic** | **Yes** | Cloud VPS with HTTPS 24/7 |
| **Pitch to Royce Aesthetics** | Optional | Local Telegram OR cloud |
| **Production paying client** | **Yes** | Cloud VPS (~$5–6/mo) |

Meta WhatsApp requires a **public HTTPS webhook URL**. Your laptop + ngrok works for testing; production needs a server that stays online.

---

## Recommended path (no n8n maintenance)

```
┌─────────────────────────────────────────┐
│  VPS ($5/mo) — DigitalOcean / Hetzner   │
│  ├── Python agent (Telegram + WhatsApp) │
│  ├── Groq API (free keys, cloud LLM)      │
│  └── Gmail SMTP alerts → your inbox     │
└─────────────────────────────────────────┘
```

**You do NOT need n8n** if you only want:
- Agent replies on WhatsApp/Telegram
- Email to `ha7165614@gmail.com` on each appointment
- Optional Telegram staff alert

That is built in now — zero extra servers.

---

## Cloud options (cheapest first)

| Provider | Cost | Notes |
|---|---|---|
| **Hetzner CX22** | ~€4/mo | Best value; Ubuntu VPS |
| **DigitalOcean Droplet** | $6/mo | Easy docs, Pakistan-friendly payments |
| **Oracle Cloud Free** | $0 | 4 ARM cores free forever; setup harder |
| **Railway / Render** | ~$5–7/mo | Easier deploy, less control |
| **Your laptop + ngrok** | Free | Demo only; not 24/7 |

### Minimum VPS specs

- 1 GB RAM — Telegram + WhatsApp + Groq (no local LLM)
- 2 GB RAM — if running Ollama 8B model on same server
- Ubuntu 22.04, Python 3.11+

---

## Deploy steps (VPS overview)

### 1. Clone your repo

```bash
git clone https://github.com/SHAH9119/Business-Automization-Agent.git
cd Business-Automization-Agent/telegram-groq-agent
pip install -r requirements.txt
```

### 2. Configure `.env` on the server

```env
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
GROQ_API_KEYS=key1,key2,key3,key4
GMAIL_SMTP_USER=ha7165614@gmail.com
GMAIL_APP_PASSWORD=...
STAFF_EMAIL=ha7165614@gmail.com
BUSINESS_PACK_DIR=../royce-aesthetics-agent
```

### 3. Run WhatsApp webhook with systemd (always on)

```bash
python -m app.whatsapp_webhook
# Use nginx + certbot for HTTPS, or Caddy reverse proxy
```

### 4. Point Meta webhook to

```
https://your-domain.com/webhook
```

See `docs/whatsapp-setup.md` for Meta configuration.

### 5. Telegram (optional, same server)

```bash
python -m app.telegram_bot
```

Use `systemd` or `pm2` to keep both running after reboot.

---

## Local LLM + Cloud — can you combine?

| Setup | Works? | Recommendation |
|---|---|---|
| **Groq on cloud VPS** | ✅ Best | Free keys, fast, Roman Urdu OK |
| **Ollama on same VPS** | ✅ | 2GB+ RAM; no external API cost |
| **Ollama on your laptop, agent on cloud** | ❌ Bad | Laptop must stay on; latency; firewall |
| **Groq dev → Ollama prod on VPS** | ✅ | Test with Groq, deploy with Ollama on VPS |

**Practical advice:**

1. **Develop** on your PC with Groq (free, fast)
2. **Deploy** to VPS with either:
   - **Groq** (simplest — keep using free keys), or
   - **Ollama** on the VPS (`curl -fsSL https://ollama.com/install.sh | sh && ollama run llama3.1:8b`) if you want zero LLM API dependency

Local LLM on your **home PC** does not replace cloud deployment for WhatsApp — Meta still needs a public server for webhooks.

---

## n8n vs Gmail SMTP — your situation

You said maintaining an n8n server is an issue. **Correct — skip n8n for now.**

| Need | Solution |
|---|---|
| Email on appointment | ✅ Gmail SMTP (built in) |
| Telegram alert | ✅ `STAFF_ALERT_CHAT_ID` |
| WhatsApp alert to staff | ✅ `WHATSAPP_STAFF_PHONE` |
| Google Calendar | Add later via n8n OR Google Calendar API |
| Google Sheets CRM | Add later via n8n OR Sheets API |

Add n8n **only** when a client pays for calendar/CRM automation and you run it on **their** VPS or charge monthly for hosting.

---

## Cost summary (your business)

| Item | Monthly cost |
|---|---|
| VPS (Hetzner/DO) | ~$5–6 |
| Groq API | $0 (free tier + key rotation) |
| Gmail alerts | $0 |
| Meta WhatsApp | $0–10 (free tier then per conversation) |
| n8n | $0 (not needed initially) |
| **Total to start** | **~$5–6/mo** |

---

## GitHub repo

Code: https://github.com/SHAH9119/Business-Automization-Agent

On the server:

```bash
git pull origin main
# restart systemd services
```

Never commit `.env` — configure secrets only on the server.
