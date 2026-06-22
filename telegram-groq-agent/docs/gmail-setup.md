# Gmail Appointment Alerts (Free — No n8n)

Send an email to your inbox whenever a customer completes an appointment request or triggers a staff handoff.

**Gmail API is free.** For a single inbox like yours, **Gmail SMTP + App Password** is simpler than full OAuth — same result, zero cost, no n8n server.

---

## Setup (5 minutes)

### 1. Enable 2-Step Verification

Google Account → **Security** → **2-Step Verification** → turn ON

### 2. Create an App Password

Google Account → **Security** → **App passwords**

- App: Mail
- Device: Other → name it `Clinic Agent`

Google gives a **16-character password** (e.g. `abcd efgh ijkl mnop`). Copy it — no spaces in `.env`.

### 3. Add to `.env`

```env
GMAIL_SMTP_USER=ha7165614@gmail.com
GMAIL_APP_PASSWORD=your16charapppassword
STAFF_EMAIL=ha7165614@gmail.com
EMAIL_FROM_NAME=Royce Aesthetics Agent
```

- `GMAIL_SMTP_USER` — the Gmail account that **sends** mail (your account)
- `STAFF_EMAIL` — who **receives** alerts (can be the same inbox)
- Never commit `.env` or the App Password to GitHub

### 4. Test

```powershell
python scripts/test_email.py
```

Check inbox + spam folder. You should see:

> **[Royal Aesthetic Clinic] Appointment Request — Test Patient**

### 5. Restart the bot

```powershell
.\scripts\run_bot.ps1
# or
.\scripts\run_whatsapp.ps1
```

When a real appointment is collected, email is sent automatically.

---

## What triggers an email?

| Event | Email subject |
|---|---|
| Full appointment collected | `[Clinic Name] Appointment Request — {name}` |
| Staff handoff / urgent | `[Clinic Name] Staff Handoff — {name}` |

Email includes: name, phone, concern, preferred day/time, channel (telegram/whatsapp).

---

## Gmail API vs SMTP vs n8n

| Method | Cost | Server to maintain? | Best for |
|---|---|---|---|
| **Gmail SMTP (this)** | Free | No | You — one inbox alert |
| Gmail API (OAuth) | Free | No | Multi-user / advanced |
| n8n + Gmail node | Free self-hosted | Yes (Docker/VPS) | Calendar + Sheets + email |
| Telegram alert only | Free | No | Demo / minimal |

**Recommendation:** Use **Gmail SMTP** for appointment emails. Skip n8n unless you need Google Calendar or Sheets.

---

## Troubleshooting

| Error | Fix |
|---|---|
| `535 Authentication failed` | Wrong App Password; use App Password not normal Gmail password |
| `534 Please log in` | 2-Step Verification not enabled |
| Email in spam | Mark as "Not spam"; add sender to contacts |
| No email on booking | Check `.env` loaded; run `test_email.py` first |

---

## Per-client deployment

For Royce Aesthetics pitch, use **your** Gmail to receive demo leads.

When they sign:
- Option A: Their Gmail App Password → `STAFF_EMAIL=clinic@gmail.com`
- Option B: Your agency inbox forwards to them

Do **not** hardcode client emails in code — always `.env` per deployment.
