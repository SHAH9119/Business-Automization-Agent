"""Checks incoming messages before they reach the AI model.

This saves API quota during spam and keeps obvious prompt-injection attempts out
of the conversation history. It is deliberately small and predictable.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
import re
import time
from typing import Callable


# These patterns cover common attempts to replace rules or steal private setup.
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+|any\s+|the\s+|your\s+)?(?:previous|prior)\s+(?:instructions|prompt|rules)", re.I),
    re.compile(r"(?:reveal|show|print|repeat|leak)\s+(?:your\s+|the\s+)?(?:system|developer)\s+(?:prompt|message|instructions)", re.I),
    re.compile(r"what\s+(?:is|are)\s+your\s+(?:system|developer)\s+(?:prompt|instructions)", re.I),
    re.compile(r"(?:jailbreak|developer\s+mode|unrestricted\s+mode)", re.I),
    re.compile(r"(?:show|reveal|print|send|give).{0,30}(?:api\s*key|secret\s*key|telegram\s*token|\.env|environment\s+variables)", re.I),
]


@dataclass(frozen=True)
class GuardDecision:
    """Result returned to the Telegram adapter for one message."""

    allowed: bool
    reason: str | None = None
    reply: str | None = None


class MessageGuard:
    """Apply message-size, spam, gibberish, and injection checks per chat."""

    def __init__(
        self,
        *,
        max_characters: int = 1500,
        burst_limit: int = 6,
        minute_limit: int = 20,
        duplicate_limit: int = 3,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_characters = max_characters
        self.burst_limit = burst_limit
        self.minute_limit = minute_limit
        self.duplicate_limit = duplicate_limit
        self.clock = clock

        # Each chat keeps only one minute of recent message times and text.
        self.recent: dict[str, deque[tuple[float, str]]] = defaultdict(deque)
        self.last_warning: dict[str, float] = {}

    def check(self, chat_id: str, text: str) -> GuardDecision:
        """Return whether a message may be sent to the receptionist agent."""
        now = self.clock()
        normalized = self._normalize(text)
        recent = self.recent[chat_id]

        while recent and now - recent[0][0] > 60:
            recent.popleft()

        recent.append((now, normalized))

        if len(text) > self.max_characters:
            return self._blocked(chat_id, now, "message too long", "Please send a shorter message so I can help clearly.")

        if self._looks_like_injection(text):
            return self._blocked(
                chat_id,
                now,
                "prompt injection",
                "I can only help with clinic services and appointments. What would you like to know?",
            )

        if self._looks_like_gibberish(text):
            return self._blocked(
                chat_id,
                now,
                "gibberish",
                "I could not understand that. Please ask about a clinic service or appointment.",
            )

        same_messages = sum(1 for _, previous in recent if previous == normalized)
        messages_in_ten_seconds = sum(1 for timestamp, _ in recent if now - timestamp <= 10)

        if same_messages >= self.duplicate_limit:
            return self._blocked(chat_id, now, "repeated message", "Please avoid repeating the same message. I am ready to help.")

        if messages_in_ten_seconds >= self.burst_limit or len(recent) >= self.minute_limit:
            return self._blocked(chat_id, now, "message rate exceeded", "You are sending messages too quickly. Please wait a moment.")

        return GuardDecision(allowed=True)

    def _blocked(self, chat_id: str, now: float, reason: str, reply: str) -> GuardDecision:
        """Send at most one warning every ten seconds during continued spam."""
        last_warning = self.last_warning.get(chat_id, -1000)
        if now - last_warning < 10:
            reply = None
        else:
            self.last_warning[chat_id] = now
        return GuardDecision(allowed=False, reason=reason, reply=reply)

    @staticmethod
    def _normalize(text: str) -> str:
        """Create a simple form used only for duplicate detection."""
        return re.sub(r"\s+", " ", text.strip().lower())

    @staticmethod
    def _looks_like_injection(text: str) -> bool:
        """Catch common direct attempts to override or expose hidden rules."""
        return any(pattern.search(text) for pattern in INJECTION_PATTERNS)

    @staticmethod
    def _looks_like_gibberish(text: str) -> bool:
        """Reject only obvious nonsense, without policing normal spelling mistakes."""
        stripped = text.strip()
        if not stripped:
            return True
        if re.fullmatch(r"[^A-Za-z0-9\u0600-\u06ff]+", stripped):
            return True
        if re.search(r"(.)\1{7,}", stripped, re.I):
            return True

        letters = re.sub(r"[^A-Za-z]", "", stripped).lower()
        one_word = not re.search(r"\s", stripped)
        return len(letters) >= 8 and one_word and not re.search(r"[aeiouy]", letters)
