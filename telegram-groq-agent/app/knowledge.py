"""Loads the clinic/business knowledge files into one text block.

For this MVP, we are not using full RAG/vector search yet. Instead, we load
the small clinic knowledge pack directly into the AI prompt.
"""

from pathlib import Path

from app.catalog import ServiceCatalog


# These are the exact files the bot reads from the business pack folder.
# If you add another knowledge file later, add its path here.
KNOWLEDGE_FILES = [
    "knowledge/clinic_profile.md",
    "knowledge/services.md",
    "knowledge/demo_prices.md",
    "knowledge/safety_rules.md",
    "flows/booking_flow.md",
    "flows/handoff_flow.md",
    "examples/sample_conversations.md",
]


def load_business_knowledge(pack_dir: Path) -> str:
    """Read all knowledge files and join them together.

    pack_dir is usually ../royce-aesthetics-agent.
    The returned text is passed to Groq so the bot knows clinic details.
    """
    sections: list[str] = []

    for relative_path in KNOWLEDGE_FILES:
        path = pack_dir / relative_path
        if path.exists():
            # Add a heading before each file so the AI can see where info came from.
            sections.append(f"\n\n--- {relative_path} ---\n{path.read_text(encoding='utf-8')}")

    if not sections:
        # Stop the app if the knowledge folder path is wrong.
        raise FileNotFoundError(f"No knowledge files found in {pack_dir}")

    return "\n".join(sections)


def load_service_catalog(pack_dir: Path) -> ServiceCatalog:
    """Load structured services and demo prices used for reliable answers."""
    return ServiceCatalog.from_file(pack_dir / "config" / "service_catalog.json")
