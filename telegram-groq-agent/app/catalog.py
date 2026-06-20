"""Structured service and demo-price lookup.

The LLM is good at understanding language, but it should not be trusted to
remember exact service availability or prices. This catalog gives Python a
reliable source for those facts before a reply is sent.
"""

import json
import re
from pathlib import Path
from typing import Any


PRICE_WORDS = ["price", "cost", "charges", "rate", "how much", "kitna", "kitni"]
SERVICE_LIST_WORDS = ["services you offer", "what services", "list services", "services available"]


def normalize(text: str) -> str:
    """Make text easier to compare with aliases."""
    lowered = text.lower().replace("-", " ")
    return re.sub(r"[^a-z0-9 ]+", " ", lowered).strip()


def contains_alias(text: str, alias: str) -> bool:
    """Match a full alias without matching it inside another word."""
    normalized_alias = normalize(alias)
    return bool(re.search(rf"\b{re.escape(normalized_alias)}\b", text))


class ServiceCatalog:
    def __init__(self, data: dict[str, Any]):
        self.data = data
        self.public = data.get("public_offerings", [])
        self.demo = data.get("demo_offerings", [])
        self.unlisted = data.get("not_publicly_listed", [])

    @classmethod
    def from_file(cls, path: Path) -> "ServiceCatalog":
        """Load the catalog JSON file."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(data)

    def evaluate(self, user_text: str, *, roman_urdu: bool = False) -> dict[str, Any] | None:
        """Return a reliable service/price answer when the catalog can help."""
        text = normalize(user_text)

        if any(phrase in text for phrase in SERVICE_LIST_WORDS):
            summary = self._service_summary(roman_urdu=roman_urdu)
            demo = self._find(text, self.demo)
            if demo and any(word in text for word in PRICE_WORDS):
                if roman_urdu:
                    summary += (
                        f"\n\n{demo['name']}: estimated price {demo['demo_price']} hai. "
                        "Final price assessment ke baad vary kar sakti hai."
                    )
                else:
                    summary += (
                        f"\n\n{demo['name']}: estimated price {demo['demo_price']}. "
                        "The final price may vary after assessment."
                    )
            return {
                "reply": summary,
                "concern": None,
                "handoff_required": False,
                "handoff_reason": None,
            }

        unlisted = self._find(text, self.unlisted)
        if unlisted:
            if roman_urdu:
                reply = (
                    f"{unlisted['name']} clinic ki current service list mein nahi hai, is liye main guess nahi karunga. "
                    "Main staff se confirmation karwa sakta hoon."
                )
            else:
                reply = (
                    f"{unlisted['name']} is not listed on the clinic's current service list, so I do not want to guess. "
                    "I can forward the question to staff for confirmation."
                )
            return {
                "reply": reply,
                "concern": unlisted["name"],
                "handoff_required": True,
                "handoff_reason": f"{unlisted['name']} is not publicly listed",
            }

        public = self._find(text, self.public)
        demo = self._find(text, self.demo)
        if not public and not demo:
            return None

        offering = public or demo
        name = offering["name"]
        wants_price = any(word in text for word in PRICE_WORDS)

        if public and roman_urdu:
            reply = f"Ji haan, {public['name']} available hai."
        elif public:
            reply = f"Yes, {public['name']} is available."
        elif roman_urdu:
            reply = f"Ji haan, {demo['name']} available hai."
        else:
            reply = f"Yes, {demo['name']} is available."

        if wants_price:
            if demo and demo.get("demo_price"):
                if roman_urdu:
                    reply += (
                        f" Estimated price {demo['demo_price']} hai. "
                        "Final price assessment ke baad vary kar sakti hai."
                    )
                else:
                    reply += (
                        f" The estimated price is {demo['demo_price']}. "
                        "The final price may vary after assessment."
                    )
            else:
                if roman_urdu:
                    reply += " Exact price assessment ke baad staff confirm karega."
                else:
                    reply += " The exact price depends on assessment and can be confirmed by staff."

        return {
            "reply": reply,
            "concern": name,
            "handoff_required": False,
            "handoff_reason": None,
        }

    def _find(self, text: str, items: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Find the item with the longest matching alias."""
        matches: list[tuple[int, dict[str, Any]]] = []
        for item in items:
            for alias in item.get("aliases", []):
                if contains_alias(text, alias):
                    matches.append((len(alias), item))
        if not matches:
            return None
        return max(matches, key=lambda match: match[0])[1]

    def _service_summary(self, *, roman_urdu: bool = False) -> str:
        """Give a readable bullet list instead of one long paragraph."""
        if roman_urdu:
            return (
                "Hamari main services mein shamil hain:\n"
                "- Skin aur acne treatment\n"
                "- Pigmentation, melasma aur freckles treatment\n"
                "- Hair-loss treatment aur hair restoration\n"
                "- Hair transplant, hair threads aur hair fillers\n"
                "- Hydrafacial\n"
                "- Laser hair removal\n"
                "- Mole, wart, cyst aur skin-growth services\n"
                "- Micropigmentation\n"
                "- Skin, hair aur nail conditions ka treatment\n\n"
                "Aap kis service ke bare mein maloomat chahte hain?"
            )
        return (
            "Our main services include:\n"
            "- Skin and acne treatment\n"
            "- Pigmentation, melasma, and freckles treatment\n"
            "- Hair-loss treatment and hair restoration\n"
            "- Hair transplant, hair threads, and hair fillers\n"
            "- Hydrafacial\n"
            "- Laser hair removal\n"
            "- Mole, wart, cyst, and other skin-growth services\n"
            "- Micropigmentation\n"
            "- Treatment for skin, hair, and nail conditions\n\n"
            "Tell me which service you would like to know more about."
        )
