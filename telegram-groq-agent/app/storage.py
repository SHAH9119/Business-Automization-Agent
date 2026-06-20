"""Local JSON storage for the demo bot.

This is a simple replacement for a real database while testing.
Later, this file can be replaced with Supabase/Postgres storage.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    """Return current time in a standard UTC string format."""
    return datetime.now(timezone.utc).isoformat()


def default_session() -> dict[str, Any]:
    """Create a fresh empty user session.

    A session means the details collected from one Telegram chat.
    """
    return {
        # The profile stores appointment details collected step by step.
        "profile": {
            "name": None,
            "phone": None,
            "concern": None,
            "preferred_day": None,
            "preferred_time": None,
            "language": None,
        },
        # Status tells us where this user is in the conversation.
        "status": "new",
        # lead_saved prevents duplicate lead files for the same request.
        "lead_saved": False,
        # handoff fields are used when a human/staff member should take over.
        "handoff_required": False,
        "handoff_reason": None,
        "last_lead_file": None,
        "updated_at": utc_now(),
    }


class JsonStorage:
    def __init__(self, data_dir: Path):
        # Main data folder, usually telegram-groq-agent/data.
        self.data_dir = data_dir

        # Create folders if they do not already exist.
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "conversations").mkdir(exist_ok=True)
        (self.data_dir / "leads").mkdir(exist_ok=True)
        (self.data_dir / "sessions").mkdir(exist_ok=True)

    def append_message(self, chat_id: str, role: str, content: str) -> None:
        """Save one chat message.

        role is either "user" or "assistant".
        """
        path = self.data_dir / "conversations" / f"{chat_id}.json"

        # Load old messages, add the new one, then save the full list again.
        messages = self.get_messages(chat_id, limit=200)
        messages.append(
            {
                "role": role,
                "content": content,
                "created_at": utc_now(),
            }
        )
        self._write_json(path, messages)

    def get_messages(self, chat_id: str, limit: int = 12) -> list[dict[str, Any]]:
        """Return recent messages for one chat.

        The agent uses this as short-term conversation memory.
        """
        path = self.data_dir / "conversations" / f"{chat_id}.json"
        if not path.exists():
            return []
        return self._read_json(path, default=[])[-limit:]

    def get_session(self, chat_id: str) -> dict[str, Any]:
        """Load collected appointment details for one chat."""
        path = self.data_dir / "sessions" / f"{chat_id}.json"
        if not path.exists():
            return default_session()

        session = self._read_json(path, default=default_session())

        # Merge with defaults so old session files still work after code changes.
        merged = default_session()
        merged.update(session)
        merged["profile"].update(session.get("profile", {}))
        return merged

    def save_session(self, chat_id: str, session: dict[str, Any]) -> None:
        """Save collected appointment details for one chat."""
        session["updated_at"] = utc_now()
        path = self.data_dir / "sessions" / f"{chat_id}.json"
        self._write_json(path, session)

    def reset_chat(self, chat_id: str) -> None:
        """Clear conversation and session for testing.

        This is used by the /reset Telegram command.
        """
        for folder in ["conversations", "sessions"]:
            path = self.data_dir / folder / f"{chat_id}.json"
            if path.exists():
                path.unlink()

    def save_lead(self, chat_id: str, lead: dict[str, Any]) -> Path:
        """Save a completed appointment request or handoff as a lead file."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = self.data_dir / "leads" / f"{timestamp}-{chat_id}.json"
        lead["chat_id"] = chat_id
        lead["created_at"] = utc_now()
        self._write_json(path, lead)
        return path

    def _read_json(self, path: Path, default: Any) -> Any:
        """Read JSON safely.

        If the file is broken or missing, return a safe default instead of crashing.
        """
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return default

    def _write_json(self, path: Path, value: Any) -> None:
        """Write JSON in a readable format."""
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
