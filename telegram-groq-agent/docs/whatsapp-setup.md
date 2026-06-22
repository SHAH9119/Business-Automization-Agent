# WhatsApp Cloud API Setup

The WhatsApp adapter uses **Meta's WhatsApp Cloud API** — you need a Meta Developer account and a WhatsApp Business phone number.

## What You Need

| Item | Where to get it |
|---|---|
| **Access Token** | Meta Developer Console → Your App → WhatsApp → API Setup |
| **Phone Number ID** | Same page (numeric ID, not the phone number) |
| **Verify Token** | You choose this — set the same value in Meta webhook config and `.env` |
| **Public HTTPS URL** | ngrok (local) or VPS domain (production) |

## Step-by-Step

### 1. Create Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. **Create App** → type **Business**
3. Add product **WhatsApp**
4. On **API Setup**, note:
   - Temporary token (for testing) or create a **System User** token (production)
   - **Phone number ID**
   - Test phone number (Meta provides one for sandbox)

### 2. Configure `.env`

```env
WHATSAPP_ACCESS_TOKEN=your_permanent_or_test_token
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_VERIFY_TOKEN=business-agent-verify
WHATSAPP_STAFF_PHONE=923001234567
N8N_WEBHOOK_URL=http://localhost:5678/webhook/clinic-lead
```

### 3. Install dependencies & run webhook server

```powershell
pip install -r requirements.txt
.\scripts\run_whatsapp.ps1
```

Server starts on **http://0.0.0.0:8000**

### 4. Expose with ngrok (local testing)

```powershell
ngrok http 8000
```

Copy the HTTPS URL, e.g. `https://abc123.ngrok.io`

### 5. Register webhook in Meta

1. Meta Developer Console → WhatsApp → **Configuration**
2. **Callback URL:** `https://abc123.ngrok.io/webhook`
3. **Verify token:** `business-agent-verify` (must match `.env`)
4. Subscribe to **messages** field
5. Click **Verify and Save**

### 6. Add test recipient

In API Setup, add your personal WhatsApp number as a **test recipient** (sandbox mode).

Send a message to the Meta test business number — the agent should reply.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Health check |
| GET | `/webhook` | Meta verification handshake |
| POST | `/webhook` | Incoming WhatsApp messages |

---

## Architecture

```text
Customer WhatsApp
       ↓
Meta Cloud API (webhook POST)
       ↓
app/whatsapp_webhook.py  (FastAPI)
       ↓
ReceptionistAgent.reply()   ← same agent as Telegram
       ↓
Groq / Gemini LLM
       ↓
Meta Graph API (send message)
       ↓
Optional: n8n webhook + staff alert
```

---

## Going Live (Production)

1. Connect a real WhatsApp Business phone number in Meta
2. Complete **Business Verification** in Meta Business Manager
3. Generate a **permanent System User token** (not the 24h test token)
4. Deploy webhook server on a VPS with HTTPS (not ngrok)
5. Set `WHATSAPP_STAFF_PHONE` to clinic owner's number for instant lead alerts

## Costs

- Meta Cloud API: first 1,000 **service conversations/month** often free; then ~$0.05–0.10 per conversation depending on country
- Groq: free tier with key rotation (already configured)
- n8n self-hosted: free

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Webhook verification fails | Check `WHATSAPP_VERIFY_TOKEN` matches Meta config exactly |
| No reply to messages | Confirm webhook subscribed to `messages`; check server logs |
| 401 from Graph API | Token expired — regenerate permanent token |
| ngrok URL changed | Update callback URL in Meta console |
