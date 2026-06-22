"""Loads the clinic/business knowledge files into one text block.

Two modes:
- load_business_knowledge()   – legacy full load, kept for tests and scripts.
- load_section_retriever()    – returns a SectionRetriever that sends only
  the files relevant to each message.  This cuts per-request token usage by
  60-80 % compared to sending everything on every call.

To customise for a new client, replace the markdown files and service_catalog.json.
No code changes are needed.

NOTE: agent_config.json lists knowledge_files/flow_files for human reference
only — the application does not read that config key.
"""

import re
from pathlib import Path

from app.catalog import ServiceCatalog


# ---------------------------------------------------------------------------
# Static file list (used by load_business_knowledge and for reference).
# ---------------------------------------------------------------------------

ALWAYS_FILES = [
    "knowledge/clinic_profile.md",   # location, hours, contact – always needed
]

TOPIC_FILES = {
    "price":   ["knowledge/prices.md"],
    "service": ["knowledge/services.md"],
    "booking": ["flows/booking_flow.md"],
    # Detailed safety wording is needed for urgent/handoff messages. Core safety
    # rules remain in ANALYZER_SYSTEM for every request.
    "handoff": ["knowledge/safety_rules.md", "flows/handoff_flow.md"],
    "faq":     ["knowledge/faq.md"],
    "visit":   ["knowledge/patient_guide.md", "knowledge/out_of_scope.md"],
}

# All files in one flat list (used by load_business_knowledge).
KNOWLEDGE_FILES = (
    ALWAYS_FILES
    + TOPIC_FILES["price"]
    + TOPIC_FILES["service"]
    + TOPIC_FILES["faq"]
    + TOPIC_FILES["visit"]
    + ["flows/greeting_flow.md"]
    + TOPIC_FILES["booking"]
    + TOPIC_FILES["handoff"]
)


# ---------------------------------------------------------------------------
# Word-boundary trigger patterns for section selection.
#
# Each pattern is compiled as a regex with \b word boundaries so that:
#   - "fee" does NOT match inside "feel" or "coffee"
#   - "book" does NOT match inside "booking" unless "book" appears alone
#   - "rate" does NOT match inside "ratedrating"
#
# Roman Urdu price words (qeemat, kitne, daam, kharcha, paisay) are included.
# ---------------------------------------------------------------------------

def _compile_triggers(*words: str) -> re.Pattern:
    """Build a single compiled regex that matches any of the words at word boundaries."""
    # Sort longest first so "how much" matches before "how".
    sorted_words = sorted(words, key=len, reverse=True)
    escaped = [re.escape(w) for w in sorted_words]
    pattern = r"\b(?:" + "|".join(escaped) + r")\b"
    return re.compile(pattern, re.IGNORECASE)


_PRICE_RE = _compile_triggers(
    # English
    "price", "cost", "charges", "rate", "how much", "fee", "fees",
    "starting from", "package", "expensive", "cheap", "affordable",
    # Roman Urdu
    "kitna", "kitni", "kitne", "qeemat", "daam", "kharcha",
    "paisay", "paisa", "mehnga", "sasta",
)

_BOOKING_RE = _compile_triggers(
    # English
    "appointment", "book", "schedule", "slot", "reserve",
    # Roman Urdu
    "milna", "appointment chahiye", "waqt", "din",
)

_SERVICE_RE = _compile_triggers(
    # English
    "service", "treatment", "procedure", "available",
    "do you offer", "do you have", "do you treat", "provide",
    "what is", "tell me about", "explain",
    # Roman Urdu
    "hota hai", "milta hai", "karte hain", "karty hain",
    "milti hai", "karta hai",
)

_HANDOFF_RE = _compile_triggers(
    # English
    "emergency", "urgent", "bleeding", "allergic", "allergy",
    "severe pain", "swelling", "infection", "fever",
    "speak to doctor", "speak to a doctor", "talk to doctor", "talk to a doctor", "human", "real person", "staff",
    "breathing",
    # Roman Urdu
    "doctor se", "insaan se", "staff se", "staff se baat", "doctor se baat",
)

_FAQ_RE = _compile_triggers(
    # English
    "cancel", "cancellation", "reschedule", "walk-in", "walk in",
    "clinic hours", "working hours", "opening hours", "closing hours",
    "clinic timing", "clinic timings", "are you open", "when do you open",
    "when do you close", "what time do you open", "what time do you close",
    "late for my appointment",
    # Roman Urdu
    "clinic kab khulti hai", "clinic kab band hoti hai", "clinic timing kya hai",
    "clinic timings kya hain", "appointment cancel", "appointment reschedule",
)

_VISIT_RE = _compile_triggers(
    # Location & directions
    "where", "address", "location", "directions", "phase 7", "kahan", "kahaan",
    "parking", "landmark", "coffee bean", "islamabad se", "rawalpindi se",
    # First visit & payment
    "first visit", "what to bring", "cnic", "payment", "card", "easypaisa",
    "jazzcash", "installment", "cash", "pehli dafa", "kya le kar",
)


# ---------------------------------------------------------------------------
# Section retriever – sends only what is relevant for each message.
# ---------------------------------------------------------------------------

class SectionRetriever:
    """Keyword-based section retriever with session-aware routing.

    Keeps every knowledge file in memory at startup (cheap – it is plain text).
    On each call it returns only the sections relevant to the user's message,
    reducing Groq input tokens by 60-80 % compared to the full load.

    Session status awareness:
    - When status is "collecting_appointment", only booking_flow is loaded
      (short follow-up answers like names and phone numbers need minimal context).
    - When the message matches price/service/handoff triggers, only those
      sections are loaded.
    - If nothing matches, a lightweight fallback (FAQ only) is sent instead
      of FAQ + services.
    """

    def __init__(self, pack_dir: Path) -> None:
        self._always = self._read(pack_dir, ALWAYS_FILES)
        self._by_topic = {
            topic: self._read(pack_dir, files)
            for topic, files in TOPIC_FILES.items()
        }

    def __call__(self, user_text: str, *, session_status: str = "") -> str:
        """Return relevant knowledge sections for the given message.

        Args:
            user_text: The customer's message.
            session_status: Current session status from storage (e.g.
                "collecting_appointment", "new", "handoff_required").
        """
        parts: list[str] = [self._always]

        wants_price = bool(_PRICE_RE.search(user_text))
        wants_booking = bool(_BOOKING_RE.search(user_text))
        wants_service = bool(_SERVICE_RE.search(user_text))
        wants_handoff = bool(_HANDOFF_RE.search(user_text))
        wants_faq = bool(_FAQ_RE.search(user_text))
        wants_visit = bool(_VISIT_RE.search(user_text))

        # Urgent/human requests take priority. Loading treatment or pricing text
        # during an emergency adds cost and can distract from safe escalation.
        if wants_handoff:
            return "\n\n".join([self._always, self._by_topic["handoff"]])

        if wants_price:
            parts.append(self._by_topic["price"])
        if wants_visit:
            parts.append(self._by_topic["visit"])
        if wants_faq:
            parts.append(self._by_topic["faq"])
        # FAQ policy questions take priority over generic words such as
        # "appointment". Cancellation/rescheduling must not reload booking flow.
        if wants_booking and not wants_faq:
            parts.append(self._by_topic["booking"])
        # Prevent loading the massive services file if a more specific topic (price/faq)
        # already triggered. This keeps the prompt well under the 6K token limit.
        if wants_service and not wants_price and not wants_faq:
            parts.append(self._by_topic["service"])

        # If any explicit topic matched, return those sections.
        # This allows asking about prices or services during the booking flow.
        if len(parts) > 1:
            return "\n\n".join(parts)

        # During appointment collection, if no other topic matched,
        # the user is likely answering short follow-ups (names, days).
        if session_status == "collecting_appointment":
            return "\n\n".join([self._always, self._by_topic["booking"]])

        # Lightweight fallback: only FAQ.
        parts.append(self._by_topic["faq"])
        return "\n\n".join(parts)

    @staticmethod
    def _read(pack_dir: Path, paths: list[str]) -> str:
        sections: list[str] = []
        for relative_path in paths:
            path = pack_dir / relative_path
            if path.exists():
                sections.append(
                    f"\n--- {relative_path} ---\n"
                    f"{path.read_text(encoding='utf-8')}"
                )
        return "\n".join(sections)


# ---------------------------------------------------------------------------
# Public loader functions.
# ---------------------------------------------------------------------------

def load_section_retriever(pack_dir: Path) -> SectionRetriever:
    """Return a SectionRetriever for per-message section selection.

    Use this in production to reduce token usage.
    The returned object is callable: retriever(user_text, session_status=...) -> str.
    """
    return SectionRetriever(pack_dir)


def load_business_knowledge(pack_dir: Path) -> str:
    """Read all knowledge files and join them (legacy full load).

    Kept for tests and scripts that pass a plain string to the agent.
    For the live bot use load_section_retriever() instead.
    """
    sections: list[str] = []
    for relative_path in KNOWLEDGE_FILES:
        path = pack_dir / relative_path
        if path.exists():
            sections.append(
                f"\n\n--- {relative_path} ---\n{path.read_text(encoding='utf-8')}"
            )
    if not sections:
        raise FileNotFoundError(f"No knowledge files found in {pack_dir}")
    return "\n".join(sections)


def load_service_catalog(pack_dir: Path) -> ServiceCatalog:
    """Load structured services and demo prices used for reliable answers."""
    return ServiceCatalog.from_file(pack_dir / "config" / "service_catalog.json")
