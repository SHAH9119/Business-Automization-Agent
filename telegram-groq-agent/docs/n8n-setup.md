# n8n Integration — Should You Use It?

## Short answer

| Stage | Recommendation |
|---|---|
| **Demo / pitch to Royce Aesthetics** | Skip n8n — built-in Telegram/WhatsApp staff alerts are enough |
| **First paying client** | Add n8n if they want email + Google Sheet + calendar |
| **Multiple clients** | Self-hosted n8n in Docker on one VPS |

**Is n8n a good option?** Yes — for your use case it is one of the best free choices because:
- You avoid writing Google OAuth, Gmail SMTP, and Calendar code yourself
- Clinic staff can change workflows in a visual UI without you redeploying Python
- One webhook from your agent → many destinations (email, sheet, calendar, SMS)

**Is Docker the best option?** For local dev and small production, **yes**:
- Free, isolated, easy reset
- Same setup on Windows (Docker Desktop), Linux VPS, or cloud
- Alternatives below if Docker is not available

---

## Options compared

| Option | Cost | Best for | Downside |
|---|---|---|---|
| **Docker n8n (self-hosted)** | Free | You, demos, 1–5 clients | You maintain the server |
| **n8n Cloud** | ~€20/mo+ | No Docker, quick start | Paid after trial |
| **Skip n8n — alerts only** | Free | Demo pitch | No email/calendar automation |
| **Direct Gmail API in Python** | Free | Single client, you code everything | OAuth setup, harder to maintain |
| **Zapier / Make** | Paid tiers | Non-technical clients | Expensive at scale |

**Recommendation for you right now:**
1. **Pitch demo** → Telegram + WhatsApp simulation + staff alert (no n8n)
2. **Client says yes** → Docker n8n on a $5–6/mo VPS + Gmail + Google Sheet
3. **Scale to 10+ clinics** → one n8n instance, separate webhook path per client

---

## When you do NOT need n8n

Your agent already:
- Saves leads to `data/leads/*.json`
- Sends staff summary to Telegram (`STAFF_ALERT_CHAT_ID`)
- Can send staff summary to WhatsApp (`WHATSAPP_STAFF_PHONE`)

That is enough for: *"New appointment — Fatima, 0312-xxx, acne, Saturday 2 PM"*

Skip n8n if the clinic is happy checking Telegram/WhatsApp alerts manually.

---

## When you SHOULD add n8n

Add n8n when the clinic wants:
- Email to `info@clinic.com` for every booking
- Google Sheet CRM (sortable patient list)
- Google Calendar tentative holds
- Different routing for urgent vs normal leads

---

# Setup Guide (Docker — recommended)

## 1. Start n8n

```powershell
cd telegram-groq-agent
docker compose up -d
```

Open **http://localhost:5678** → create account.

> No Docker? Install n8n globally: `npm install -g n8n` then run `n8n start` (same port 5678).

## 2. Import the sample workflow (optional)

1. In n8n: **Workflows** → **Import from File**
2. Select `docs/n8n-workflow-clinic-lead.json`
3. Open the workflow → **Webhook** node → copy the **Production URL**
4. **Activate** the workflow (toggle top-right)

Or create manually:

1. **New workflow** → add **Webhook** node
2. HTTP Method: `POST`, Path: `clinic-lead`
3. Add **Respond to Webhook** node (returns `{ "ok": true }`)
4. Connect Webhook → Respond to Webhook
5. Activate workflow

Production URL example:
```
http://localhost:5678/webhook/clinic-lead
```

## 3. Connect the agent

In `.env`:

```env
N8N_WEBHOOK_URL=http://localhost:5678/webhook/clinic-lead
```

Restart Telegram or WhatsApp bot.

## 4. Test connectivity (no real booking needed)

```powershell
python scripts/test_n8n_webhook.py
```

Check n8n → **Executions** tab — you should see a successful run.

---

## Webhook payload (what n8n receives)

```json
{
  "event": "lead_saved",
  "channel": "whatsapp",
  "chat_id": "wa:923001234567",
  "business_name": "Royal Aesthetic Clinic",
  "tenant_id": "royce_aesthetics_phase7_rawalpindi",
  "status": "appointment_request",
  "profile": {
    "name": "Fatima Malik",
    "phone": "0312-5678901",
    "concern": "Laser hair removal — underarms",
    "preferred_day": "Tuesday",
    "preferred_time": "2 PM",
    "language": "roman_urdu"
  },
  "staff_summary": "New appointment request (whatsapp)\n...",
  "handoff_reason": null,
  "lead_file": "20260622-120000-wa:923001234567.json"
}
```

`status`: `appointment_request` or `handoff_required`

---

## Extend the workflow (after basic webhook works)

### Add Google Sheets row

```
Webhook → Google Sheets (Append)
```

Columns: `{{ $json.profile.name }}`, `{{ $json.profile.phone }}`, `{{ $json.profile.concern }}`, `{{ $json.profile.preferred_day }}`, `{{ $json.profile.preferred_time }}`, `{{ $json.channel }}`, `{{ $json.status }}`

### Add Gmail email

```
Webhook → Gmail (Send)
```

- **To:** clinic email
- **Subject:** `New booking — {{ $json.profile.name }}`
- **Body:** `{{ $json.staff_summary }}`

### Add Google Calendar (tentative)

```
Webhook → Google Calendar (Create Event)
```

- **Title:** `{{ $json.profile.concern }} — {{ $json.profile.name }}`
- **Description:** `{{ $json.staff_summary }}`
- **Start/End:** use a Code node to parse `preferred_day` + `preferred_time`, or create a 30-min block at a default time until you add smarter parsing

> Calendar events are **tentative** — staff still confirms with the patient by phone.

### Route urgent handoffs differently

```
Webhook → IF (status equals handoff_required)
            ├─ true  → Gmail (urgent subject) + Telegram
            └─ false → Google Sheets + Gmail (normal)
```

---

## Full stack diagram

```
Customer WhatsApp/Telegram
         ↓
   ReceptionistAgent
         ↓
   Lead saved (data/leads/)
         ↓
   ┌─────┴─────┐
   ↓           ↓
Staff alert   n8n webhook
(TG / WA)          ↓
              Gmail / Sheet / Calendar
```

---

## Production checklist

- [ ] n8n on VPS with Docker (`docker compose up -d`)
- [ ] Use HTTPS for n8n if exposed publicly (reverse proxy + SSL)
- [ ] Add webhook auth in n8n for production
- [ ] `N8N_WEBHOOK_URL` in `.env` only — never commit
- [ ] n8n failures do **not** block customer replies (fire-and-forget)

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `test_n8n_webhook.py` fails | Workflow must be **Active**; URL must match exactly |
| n8n not reachable from agent | Use `host.docker.internal` on Windows if agent runs outside Docker |
| Google nodes fail | Connect Google account in n8n credentials tab first |
| Duplicate emails | Add IF node: only send email when `event = lead_saved` |
