"""Load tenant settings from the business pack's agent_config.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_ESCALATION_KEYWORDS = [
    "emergency",
    "urgent",
    "bleeding",
    "breathing",
    "allergic",
    "allergy",
    "severe pain",
    "swelling",
    "infection",
    "fever",
]


class BusinessConfig:
    """Runtime view of config/agent_config.json for one tenant."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    @classmethod
    def from_pack_dir(cls, pack_dir: Path) -> BusinessConfig:
        path = pack_dir / "config" / "agent_config.json"
        if not path.exists():
            return cls({})
        return cls(json.loads(path.read_text(encoding="utf-8")))

    @property
    def business_name(self) -> str:
        return self.data.get("business_name") or "the clinic"

    @property
    def brand_name(self) -> str:
        return self.data.get("brand_name") or self.business_name

    @property
    def tenant_id(self) -> str:
        return self.data.get("tenant_id") or "default"

    @property
    def phone(self) -> str:
        contact = self.data.get("contact") or {}
        return contact.get("phone") or contact.get("whatsapp") or ""

    @property
    def whatsapp(self) -> str:
        contact = self.data.get("contact") or {}
        return contact.get("whatsapp") or contact.get("phone") or ""

    @property
    def website(self) -> str:
        return (self.data.get("contact") or {}).get("website") or ""

    @property
    def location_line(self) -> str:
        location = self.data.get("location") or {}
        area = location.get("area") or ""
        city = location.get("city") or ""
        if area and city:
            return f"{area}, {city}"
        return area or city or ""

    @property
    def hours_open(self) -> str:
        return (self.data.get("hours") or {}).get("open") or "12:00 PM"

    @property
    def hours_close(self) -> str:
        return (self.data.get("hours") or {}).get("close") or "05:00 PM"

    @property
    def hours_days(self) -> str:
        return (self.data.get("hours") or {}).get("days") or "Monday to Sunday"

    def hours_text(self) -> str:
        return f"{self.hours_days}, {self.hours_open} – {self.hours_close}"

    @property
    def persona(self) -> dict[str, Any]:
        return self.data.get("agent_persona") or {}

    @property
    def greeting_en(self) -> str:
        custom = self.persona.get("greeting_en")
        if custom:
            return custom
        location = self.location_line
        suffix = f" — {location}" if location else ""
        return (
            f"Hello! 👋 Welcome to {self.business_name} ({self.brand_name}){suffix}.\n\n"
            "I'm your virtual assistant. I can help with:\n"
            "• 💆 Skin treatments & procedures\n"
            "• 💇 Hair restoration & transplants\n"
            "• 💉 Botox, fillers & aesthetic treatments\n"
            "• 📅 Booking an appointment\n"
            "• 💰 Estimated pricing\n\n"
            "How can I assist you today?"
        )

    @property
    def greeting_ur(self) -> str:
        custom = self.persona.get("greeting_ur")
        if custom:
            return custom
        location = self.location_line
        suffix = f" — {location}" if location else ""
        return (
            f"Salam! 👋 {self.business_name} ({self.brand_name}) mein khush aamdeed{suffix}.\n\n"
            "Main aapki madad kar sakta hoon:\n"
            "• 💆 Skin treatments\n"
            "• 💇 Hair restoration & transplant\n"
            "• 💉 Botox, fillers & aesthetic procedures\n"
            "• 📅 Appointment booking\n"
            "• 💰 Estimated prices\n\n"
            "Kya poochna chahte hain?"
        )

    def greeting(self, *, roman_urdu: bool = False) -> str:
        return self.greeting_ur if roman_urdu else self.greeting_en

    @property
    def help_en(self) -> str:
        phone_line = f"\n• Urgent matters: {self.phone}" if self.phone else ""
        return (
            "You can ask me about:\n"
            "• Skin treatments (acne, pigmentation, HydraFacial, peels, laser)\n"
            "• Hair services (transplant, PRP, laser hair removal)\n"
            "• Aesthetic injectables (Botox, fillers)\n"
            "• Prices and packages\n"
            "• Clinic location & timing\n"
            "• Booking an appointment"
            f"{phone_line}\n\n"
            "Type your question or concern and I'll help right away."
        )

    @property
    def help_ur(self) -> str:
        phone_line = f"\n• Urgent: {self.phone}" if self.phone else ""
        return (
            "Aap yeh pooch sakte hain:\n"
            "• Skin treatments (acne, pigmentation, HydraFacial, laser)\n"
            "• Hair services (transplant, PRP, laser hair removal)\n"
            "• Botox, fillers\n"
            "• Prices aur packages\n"
            "• Clinic location & timing\n"
            "• Appointment booking"
            f"{phone_line}\n\n"
            "Apna sawal likhein, main madad karunga."
        )

    def help_text(self, *, roman_urdu: bool = False) -> str:
        return self.help_ur if roman_urdu else self.help_en

    @property
    def escalation_keywords(self) -> list[str]:
        configured = self.data.get("escalation_keywords") or []
        merged = list(DEFAULT_ESCALATION_KEYWORDS)
        for word in configured:
            normalized = str(word).strip().lower()
            if normalized and normalized not in merged:
                merged.append(normalized)
        return merged

    @property
    def time_windows(self) -> list[dict[str, str]]:
        windows = self.data.get("time_windows") or []
        if windows:
            return windows
        return [
            {"label": "Early Afternoon", "from": "12:00", "to": "14:00"},
            {"label": "Mid Afternoon", "from": "14:00", "to": "16:00"},
            {"label": "Late Afternoon", "from": "16:00", "to": "17:00"},
        ]

    def preferred_time_prompt(self, *, roman_urdu: bool = False) -> str:
        open_label = self.hours_open.replace(":00", "").replace(" ", " ")
        close_label = self.hours_close.replace(":00", "").replace(" ", " ")
        if roman_urdu:
            return f"{open_label} se {close_label} ke darmiyan kaunsa time suit karega?"
        return f"What time window would suit you between {self.hours_open} and {self.hours_close}?"

    def contact_line(self, *, roman_urdu: bool = False) -> str:
        if not self.phone:
            return ""
        if roman_urdu:
            return f"Urgent ho to **{self.phone}** par call ya WhatsApp karein."
        return f"If this is urgent, please call or WhatsApp **{self.phone}**."
