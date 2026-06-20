# Greeting Flow — Royal Aesthetic Clinic

The greeting flow runs at the start of every new conversation. It sets the tone, establishes context, and identifies the patient's intent before entering any other flow.

---

## Entry Point — When Patient First Messages

Detect language from first message. Respond in the same language.

### English Greeting

> "Hello! 👋 Welcome to Royal Aesthetic Clinic (Royce Aesthetics) — Bahria Town Phase 7, Rawalpindi.
>
> I'm your virtual assistant. I can help you with:
> - 💆 Skin treatments & procedures
> - 💇 Hair restoration & transplants
> - 💉 Botox, fillers & aesthetic treatments
> - 📅 Booking an appointment
> - 💰 Estimated pricing
>
> How can I assist you today?"

### Roman Urdu Greeting

> "Salam! 👋 Royal Aesthetic Clinic (Royce Aesthetics) mein khush aamdeed — Bahria Town Phase 7, Rawalpindi.
>
> Main aapki madad kar sakta hoon:
> - 💆 Skin treatments
> - 💇 Hair restoration & transplant
> - 💉 Botox, fillers & aesthetic procedures
> - 📅 Appointment booking
> - 💰 Estimated prices
>
> Kya poochna chahte hain?"

---

## Intent Detection After Greeting

After the greeting (or if patient skips to a direct question), detect intent:

| Intent | Keywords | Route To |
|---|---|---|
| Appointment | "appointment", "book", "visit", "consultation", "slot", "milna hai" | Booking Flow |
| Price | "price", "cost", "kitna", "charges", "fee", "rate" | Price answer + Booking offer |
| Service info | "do you have", "what treatments", "kya hota hai", "available hai" | Services answer |
| Location | "where", "address", "kahan", "location", "kahaan" | Location reply |
| Hours | "timing", "hours", "kab open", "when open" | Hours reply |
| Urgent | "emergency", "allergic", "reaction", "severe", "help me" | Emergency escalation |
| Human request | "doctor", "human", "real person", "staff" | Human handoff |

---

## Quick Reply Options (if platform supports buttons)

After greeting, show quick reply options:

1. 📅 Book Appointment
2. 💰 Check Prices
3. 💆 Skin Treatments
4. 💇 Hair Services
5. 📍 Location & Hours
6. 🆘 Urgent Help

---

## Returning Patient Detection

If patient says "I came before", "returning patient", "I've been here", or gives their name and it matches a past entry:

> "Welcome back! 😊 How can I help you today? Would you like to book a follow-up session or do you have a new concern?"

---

## End of Greeting — Transition

Once intent is identified, transition naturally into the appropriate flow without re-asking the greeting.
