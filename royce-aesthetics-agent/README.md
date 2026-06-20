# Royce Aesthetics — WhatsApp Agent Documentation

## Project Overview

This is the complete knowledge pack and agent configuration for the **Royal Aesthetic Clinic (Royce Aesthetics)** WhatsApp AI receptionist agent. Built to demonstrate a reusable, customizable AI agent pipeline for aesthetic clinics — pitchable to the clinic as a turnkey product.

---

## About the Business

| Detail | Value |
|---|---|
| **Clinic** | Royal Aesthetic Clinic / Royce Aesthetics |
| **Location** | Bahria Town Phase 7, Rawalpindi |
| **Phone** | 0335-6377775 |
| **Hours** | 7 days a week, 12 PM – 5 PM |
| **Experience** | 14+ years dermatology |
| **Patients** | 16,200+ served |
| **Website** | royceaesthetics.com |

---

## Why This Agent Exists

Aesthetic clinics like Royce Aesthetics receive dozens of repetitive WhatsApp messages every day:
- "Do you do laser hair removal?"
- "Hydrafacial ki price kya hai?"
- "Appointment book karni hai"
- "Kahan located ho?"

A human receptionist handles these manually. This agent automates 80% of those interactions — answering instantly, collecting appointment details, and passing complex cases to human staff.

---

## Project Structure

```
royce-aesthetics-agent/
├── README.md                         ← This file
├── config/
│   ├── agent_config.json             ← Core clinic settings & agent settings
│   └── service_catalog.json          ← All services with aliases & prices (structured)
├── knowledge/
│   ├── clinic_profile.md             ← Full clinic overview, location, team, philosophy
│   ├── services.md                   ← Detailed service descriptions (human-readable)
│   ├── prices.md                     ← Complete pricing guide for all services
│   ├── safety_rules.md               ← What the agent can/cannot do + boundaries
│   └── faq.md                        ← 40+ FAQ questions with exact agent responses
├── flows/
│   ├── greeting_flow.md              ← Greeting and intent detection
│   ├── booking_flow.md               ← Appointment intake workflow
│   └── handoff_flow.md               ← Human escalation workflow
└── examples/
    └── sample_conversations.md       ← 10 realistic demo conversations
```

---

## Agent Capabilities

| Capability | Status |
|---|---|
| Answer service questions | ✅ |
| Answer FAQ instantly | ✅ |
| Give estimated pricing | ✅ |
| Collect appointment requests | ✅ |
| Respond in English / Urdu / Roman Urdu | ✅ |
| Detect and escalate emergencies | ✅ |
| Forward to human staff | ✅ |
| Summarize conversation for staff | ✅ |
| Handle returning patients | ✅ |

---

## Services Covered

- **Skin:** HydraFacial, Chemical Peels, Microneedling, Carbon Laser Peel, HIFU, Thread Lift, Glutathione, Skin Boosters, Mole/Wart/Cyst Removal
- **Hair:** FUE/DHI Transplant, Beard Transplant, Eyebrow Transplant, Hair PRP, Hair Fillers, Hair Threads, Scalp Micropigmentation
- **Laser:** Laser Hair Removal (all body areas), Laser Pigmentation, Laser Resurfacing
- **Injectables:** Botox (all areas), Lip Fillers, Cheek Fillers, Jawline, Tear Trough, Non-Surgical Rhinoplasty
- **Medical Dermatology:** Acne, Rosacea, Melasma, Eczema, Psoriasis, Urticaria, Infections, Vitiligo, and 20+ conditions
- **Packages:** Smooth Face, Beautiful Lips, Chic Look, Healthy Skin, Soft Skin, No Mole

---

## How to Customize for Another Business

This pipeline is designed to be **business-agnostic**. To deploy for a different clinic or business:

1. **Update `config/agent_config.json`** — Replace clinic name, location, phone, hours, credentials
2. **Rewrite `knowledge/clinic_profile.md`** — New clinic's profile, team, facilities
3. **Rewrite `knowledge/services.md`** — New service descriptions
4. **Rewrite `knowledge/prices.md`** — New pricing guide
5. **Update `config/service_catalog.json`** — New services with aliases and prices
6. **Update `knowledge/faq.md`** — New FAQ answers
7. **Update `examples/sample_conversations.md`** — New sample conversations
8. No code changes required — only documentation/config files.

This works for: hospitals, dental clinics, physiotherapy, spas, beauty salons, doctors' offices, and more.

---

## Agent Boundaries (Non-Negotiable)

- ❌ No diagnosis
- ❌ No prescriptions or medication recommendations
- ❌ No treatment guarantees or result promises
- ❌ No emergency medical triage
- ✅ Always refer complex questions to the dermatologist
- ✅ Always give prices as "estimated" or "starting from"

---

## Demo Disclaimer

> *"This is an AI receptionist demo built from publicly available information. It does not make medical decisions, does not officially represent the clinic, and all prices are estimates. Actual prices and treatment plans are confirmed by the clinic's dermatologist."*

---

## Pitch Summary (For Client Presentation)

> Royal Aesthetic Clinic currently handles all patient queries manually via WhatsApp. This AI receptionist agent can:
> - Respond **instantly, 24/7** — even when staff are busy or offline
> - Answer the **most common 80% of questions** automatically
> - **Collect appointment details** and forward to staff
> - Handle **Urdu, Roman Urdu, and English** — just like your patients speak
> - **Escalate urgent cases** to human staff immediately
> - Save your receptionist hours of repetitive messaging daily
>
> This is a **plug-and-play product** — your knowledge, your branding, your patients.
