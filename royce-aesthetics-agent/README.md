# Royce Aesthetics — Complete Agent Knowledge Pack

> **Royal Aesthetic Clinic · Bahria Town Phase 7, Rawalpindi**  
> AI WhatsApp / SMS / Voice receptionist — demo-ready knowledge pack for client pitch

---

## What This Is

This folder is the **complete business pack** for the Royce Aesthetics AI agent. It contains everything the bot needs to act as a professional clinic receptionist:

- Full service catalog with **60+ treatments**
- **Detailed PKR pricing** for every major service
- **40+ FAQ** answers in English and Roman Urdu
- Booking, greeting, and handoff flows
- Safety boundaries and off-topic handling
- 10+ sample conversations for demo

The runtime code lives in `../telegram-groq-agent/` — this folder is **swappable** for any other business (hospital, dental, spa) by replacing these files.

---

## About the Clinic

| Detail | Value |
|---|---|
| **Clinic** | Royal Aesthetic Clinic |
| **Brand** | Royce Aesthetics |
| **Location** | Expressway, Sector F, above Coffee Bean, **Bahria Town Phase 7**, Rawalpindi |
| **Phone / WhatsApp** | **0335-6377775** |
| **Hours** | 7 days · **12 PM – 5 PM** |
| **Experience** | 14+ years dermatology |
| **Patients** | 16,200+ served |
| **Languages** | English · Roman Urdu (when patient writes Urdu) |
| **Website** | royceaesthetics.com |

---

## Complete File Map

```
royce-aesthetics-agent/
├── README.md                          ← This file (pitch + structure)
├── config/
│   ├── agent_config.json              ← Clinic metadata, persona, hours, escalation
│   └── service_catalog.json           ← 60+ services, 45+ priced demo offerings
├── knowledge/
│   ├── clinic_profile.md              ← Full clinic identity, team, facilities
│   ├── services.md                      ← Detailed treatment descriptions
│   ├── prices.md                        ← Complete PKR pricing guide (all categories)
│   ├── faq.md                           ← 50+ Q&A (English + Roman Urdu)
│   ├── patient_guide.md                 ← Parking, first visit, payment, what to bring
│   ├── safety_rules.md                  ← Medical boundaries + off-topic rules
│   └── out_of_scope.md                  ← How to handle irrelevant conversations
├── flows/
│   ├── greeting_flow.md                 ← First message + intent detection
│   ├── booking_flow.md                  ← Appointment intake workflow
│   └── handoff_flow.md                  ← Human escalation workflow
└── examples/
    └── sample_conversations.md          ← Realistic demo conversations
```

---

## Services & Pricing Summary

### Medical Dermatology (25+ conditions)
Acne, melasma, eczema, psoriasis, vitiligo, rosacea, infections, warts, moles, and more.  
Consultation from **PKR 2,500**.

### Aesthetic Skin
| Treatment | Starting From |
|---|---|
| HydraFacial | PKR 8,000 / session |
| Chemical Peel | PKR 3,000 / session |
| Microneedling | PKR 5,000 / session |
| Microneedling + PRP | PKR 10,000 / session |
| Carbon Laser Peel | PKR 6,000 / session |
| HIFU | PKR 15,000 / session |
| Thread Lift | PKR 20,000 |
| Glutathione Drip | PKR 4,000 / session |
| Skin Booster / Profhilo | PKR 15,000 / session |

### Hair
| Treatment | Starting From |
|---|---|
| Hair PRP | PKR 10,000 / session |
| FUE Hair Transplant | PKR 60,000 |
| DHI Transplant | PKR 80,000 / 1,000 grafts |
| Beard Transplant | PKR 50,000 |
| Eyebrow Transplant | PKR 50,000 |
| Scalp Micropigmentation | PKR 25,000 |

### Laser Hair Removal
| Area | Starting From |
|---|---|
| Upper Lip | PKR 2,000 / session |
| Underarms | PKR 3,000 / session |
| Full Face | PKR 5,000 / session |
| Full Body | PKR 20,000 / session |
| 6-Session Full Body Package | PKR 80,000 |

### Injectables
| Treatment | Starting From |
|---|---|
| Botox (per area) | PKR 10,000 |
| Lip Filler | PKR 15,000 |
| Cheek Filler | PKR 20,000 / side |
| Jawline Filler | PKR 25,000 |
| Tear Trough Filler | PKR 25,000 |
| Non-Surgical Rhinoplasty | PKR 25,000 |

### Branded Packages
Smooth Face · Beautiful Lips · Chic Look · Healthy Skin · Soft Skin · No Mole · Bridal Glow  
From **PKR 8,000 – 60,000** depending on package.

*Full pricing tables in `knowledge/prices.md`.*

---

## Agent Capabilities

| Capability | Status |
|---|---|
| Answer service questions (60+ treatments) | ✅ |
| Give estimated PKR pricing (45+ priced items) | ✅ |
| Collect appointment requests | ✅ |
| English + Roman Urdu responses | ✅ |
| Detect emergencies & escalate | ✅ |
| Forward leads to staff (Telegram alert) | ✅ |
| Reject off-topic / irrelevant chat | ✅ |
| Refuse diagnosis & treatment recommendations | ✅ |
| Handle returning patients | ✅ |
| Parking, payment, first-visit guidance | ✅ |

---

## Agent Boundaries

| Allowed | Not Allowed |
|---|---|
| Describe services & estimated prices | Diagnose skin/hair conditions |
| Collect appointment details | Recommend specific treatments |
| Explain general treatment info | Promise results or guarantees |
| Escalate to human staff | Handle medical emergencies |
| Redirect off-topic chat | Entertain jokes, homework, personal chat |

---

## Customization Guide — Deploy for Any Business

This pipeline is **business-agnostic**. To create an agent for a hospital, dental clinic, or any company:

1. **Copy this folder** → rename (e.g. `city-hospital-agent/`)
2. **Update `config/agent_config.json`** — name, location, phone, hours, persona
3. **Rewrite `knowledge/*.md`** — profile, services, prices, FAQ
4. **Update `config/service_catalog.json`** — services + demo prices
5. **Update `flows/*.md`** — booking fields, time windows
6. **Update `examples/sample_conversations.md`** — demo scripts
7. **Set `BUSINESS_PACK_DIR`** in `.env` → no code changes needed

### Future platform improvements (code-side)
- Load `agent_config.json` at runtime (persona, greetings, hours)
- WhatsApp Cloud API adapter (same `ReceptionistAgent.reply()`)
- Voice adapter (STT → agent → TTS)
- Google Calendar / email booking integration

---

## Demo Disclaimer

> *This is an AI receptionist demo built for presentation purposes. It does not make medical decisions, does not officially represent the clinic until deployed with their approval, and all prices are estimates. Actual prices and treatment plans are confirmed by the clinic's dermatologist.*

---

## Client Pitch — One Page Summary

**Problem:** Royce Aesthetics receives dozens of repetitive WhatsApp messages daily — price checks, service questions, appointment requests — all handled manually by reception staff.

**Solution:** An AI receptionist that:
- Responds **instantly, 24/7** (even outside 12–5 PM hours)
- Answers **80% of common questions** in English and Roman Urdu
- Knows **60+ services** and **45+ price points**
- **Collects appointment requests** and alerts staff immediately
- **Escalates emergencies** and complex cases to humans
- **Refuses off-topic chat** — no wasted staff time or API costs

**Location-aware:** Knows Phase 7 address, Coffee Bean landmark, parking, Islamabad/Rawalpindi directions.

**Cost to clinic:** Fraction of a receptionist's daily time on repetitive messaging.

**Deployment:** WhatsApp Business API → same agent core. Telegram used for free demo/testing today.

**Next step:** Live demo on Telegram → WhatsApp integration → staff calendar sync.

---

## Quick Test Questions (For Demo)

Try these during a live demo to impress the client:

| Question | Expected Behavior |
|---|---|
| "Clinic kahan hai?" | Phase 7, Coffee Bean landmark, Roman Urdu |
| "Underarms laser kitni hai?" | PKR 3,000 starting, package mention |
| "Hair transplant cost?" | PKR 60,000 starting, graft assessment note |
| "Mujhe kya treatment chahiye acne ke liye?" | Boundary — no diagnosis, offer consultation |
| "Tell me a joke" | Off-topic redirect |
| "Appointment book karni hai" | Starts booking flow — name, phone, concern, day, time |
| "Face swollen after cream, help!" | Emergency escalation + phone number |
