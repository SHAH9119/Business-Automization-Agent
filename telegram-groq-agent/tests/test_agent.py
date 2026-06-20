"""Tests for the receptionist agent.

These tests do not call real Groq or Telegram.
They use fake AI replies so we can test the logic for free.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from app.agent import ReceptionistAgent
from app.catalog import ServiceCatalog
from app.storage import JsonStorage


class FakeGroq:
    """Fake Groq client used only for tests.

    Instead of calling the internet, it returns prepared responses one by one.
    """

    def __init__(self, responses):
        self.responses = list(responses)

    async def chat_json(self, messages):
        # Pretend Groq returned a JSON response.
        return json.dumps(self.responses.pop(0))

    async def chat(self, messages):
        # Backup method if the agent falls back to normal chat.
        return json.dumps(self.responses.pop(0))


class ReceptionistAgentTest(unittest.TestCase):
    def test_collects_and_saves_appointment_request(self):
        """User gives appointment details step by step, then one lead is saved."""

        # These are fake AI analysis results for each user message.
        responses = [
            {
                "intent": "booking",
                "reply": "Yes, the clinic handles acne concerns.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": "acne",
                    "preferred_day": "tomorrow",
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": False,
                "handoff_reason": None,
            },
            {
                "intent": "booking",
                "reply": "",
                "extracted": {
                    "name": "Ali",
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": False,
                "handoff_reason": None,
            },
            {
                "intent": "booking",
                "reply": "",
                "extracted": {
                    "name": None,
                    "phone": "03001234567",
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": False,
                "handoff_reason": None,
            },
            {
                "intent": "booking",
                "reply": "",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": "2 PM",
                    "language": "english",
                },
                "handoff_required": False,
                "handoff_reason": None,
            },
        ]

        # tempfile creates a temporary data folder that gets deleted after the test.
        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic timing is 12 PM to 5 PM.",
            )

            # Simulate a real conversation.
            reply1, alert1 = asyncio.run(agent.reply("123", "I want an appointment for acne tomorrow"))
            reply2, alert2 = asyncio.run(agent.reply("123", "Ali"))
            reply3, alert3 = asyncio.run(agent.reply("123", "03001234567"))
            reply4, alert4 = asyncio.run(agent.reply("123", "2 pm"))

            # Bot should ask for missing details in order.
            self.assertIn("name", reply1.lower())
            self.assertIn("phone", reply2.lower())
            self.assertIn("time", reply3.lower())

            # Once all details are collected, the bot should confirm it is noted.
            self.assertIn("noted", reply4.lower())

            # No staff alert before the lead is complete.
            self.assertIsNone(alert1)
            self.assertIsNone(alert2)
            self.assertIsNone(alert3)

            # Staff alert appears after the lead is complete.
            self.assertIsNotNone(alert4)

            # Exactly one lead file should be created.
            self.assertEqual(len(list((Path(tmp) / "leads").glob("*.json"))), 1)

    def test_urgent_message_creates_handoff(self):
        """Urgent/medical message should create a human handoff lead."""

        responses = [
            {
                "intent": "urgent",
                "reply": "",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": "allergic reaction",
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": True,
                "handoff_reason": "Possible allergic reaction",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic timing is 12 PM to 5 PM.",
            )

            reply, alert = asyncio.run(agent.reply("123", "My face is swollen after a cream allergic reaction"))

            # Bot should not diagnose; it should tell user to seek urgent care.
            self.assertIn("urgent care", reply.lower())

            # Staff alert should be created.
            self.assertIsNotNone(alert)

            # A lead file should be saved for staff review.
            self.assertEqual(len(list((Path(tmp) / "leads").glob("*.json"))), 1)

    def test_unknown_question_creates_normal_handoff(self):
        """If the bot does not know something, it should not guess."""

        responses = [
            {
                "intent": "handoff",
                "reply": "",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": "unknown price question",
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": True,
                "handoff_reason": "Question is not covered by clinic knowledge",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic timing is 12 PM to 5 PM.",
            )

            reply, alert = asyncio.run(agent.reply("123", "What is the exact hydrafacial price?"))

            # Bot should avoid guessing and tell user staff can reach out.
            self.assertIn("do not want to guess", reply.lower())
            self.assertIn("staff", reply.lower())
            self.assertIsNotNone(alert)
            self.assertEqual(len(list((Path(tmp) / "leads").glob("*.json"))), 1)

    def test_handoff_does_not_request_details_already_collected(self):
        """Unknown-answer handoff should not ask for name/phone twice."""

        responses = [
            {
                "intent": "handoff",
                "reply": "",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": "unlisted question",
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": True,
                "handoff_reason": "Not covered by clinic knowledge",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonStorage(Path(tmp))
            session = storage.get_session("123")
            session["profile"]["name"] = "Ali"
            session["profile"]["phone"] = "03001234567"
            storage.save_session("123", session)

            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=storage,
                business_knowledge="Clinic timing is 12 PM to 5 PM.",
            )

            reply, alert = asyncio.run(agent.reply("123", "Tell me the exact price"))

            self.assertIn("forwarded", reply.lower())
            self.assertNotIn("share your name", reply.lower())
            self.assertNotIn("share your phone", reply.lower())
            self.assertIsNotNone(alert)

    def test_known_service_question_does_not_force_booking(self):
        """Asking about a service should answer it without immediately asking for a name."""

        responses = [
            {
                "intent": "faq",
                "reply": "I am not sure.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": True,
                "handoff_reason": "LLM did not know",
            }
        ]

        catalog_path = (
            Path(__file__).resolve().parents[2]
            / "royce-aesthetics-agent"
            / "config"
            / "service_catalog.json"
        )

        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic information",
                service_catalog=ServiceCatalog.from_file(catalog_path),
            )

            reply, alert = asyncio.run(agent.reply("123", "Do you offer hydrafacial and what is its price?"))

            self.assertIn("pkr 8,000", reply.lower())
            self.assertNotIn("may i have your name", reply.lower())
            self.assertIsNone(alert)

    def test_english_message_overrides_old_roman_urdu_language(self):
        """An English message must not receive a Roman Urdu sentence."""

        responses = [
            {
                "intent": "out_of_scope",
                "reply": "I can only help with clinic information and appointments.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "roman_urdu",
                },
                "handoff_required": True,
                "handoff_reason": "Unrelated question",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonStorage(Path(tmp))
            session = storage.get_session("123")
            session["profile"]["language"] = "roman_urdu"
            storage.save_session("123", session)

            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=storage,
                business_knowledge="Clinic information",
            )

            reply, alert = asyncio.run(agent.reply("123", "Can you give me Python code for a DSA problem?"))

            self.assertEqual(reply, "I can only help with clinic information and appointments.")
            self.assertNotIn("aap", reply.lower())
            self.assertIsNone(alert)
            self.assertEqual(storage.get_session("123")["profile"]["language"], "english")

    def test_cancellation_question_does_not_start_booking(self):
        """A cancellation-policy question must not trigger appointment collection."""

        responses = [
            {
                "intent": "faq",
                "reply": "Cancellation depends on clinic policy. Staff can confirm the details.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "roman_urdu",
                },
                "handoff_required": False,
                "handoff_reason": None,
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            storage = JsonStorage(Path(tmp))
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=storage,
                business_knowledge="Clinic information",
            )

            reply, alert = asyncio.run(agent.reply("123", "Can I cancel an appointment after booking?"))

            self.assertIn("cancellation", reply.lower())
            self.assertNotIn("may i have your name", reply.lower())
            self.assertEqual(storage.get_session("123")["status"], "new")
            self.assertIsNone(alert)

    def test_roman_urdu_message_gets_roman_urdu_catalog_reply(self):
        """Current Roman Urdu wording should produce a Roman Urdu service reply."""

        responses = [
            {
                "intent": "faq",
                "reply": "Hydrafacial is available.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": None,
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "english",
                },
                "handoff_required": False,
                "handoff_reason": None,
            }
        ]

        catalog_path = (
            Path(__file__).resolve().parents[2]
            / "royce-aesthetics-agent"
            / "config"
            / "service_catalog.json"
        )

        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic information",
                service_catalog=ServiceCatalog.from_file(catalog_path),
            )

            reply, alert = asyncio.run(agent.reply("123", "Hydrafacial ki price kya hai?"))

            self.assertIn("available hai", reply.lower())
            self.assertIn("pkr 8,000", reply.lower())
            self.assertIsNone(alert)

    def test_handoff_with_existing_answer_does_not_repeat_itself(self):
        """A useful LLM answer should be followed only by the missing contact request."""

        responses = [
            {
                "intent": "handoff",
                "reply": "Cancellation policy staff confirm kar sakta hai.",
                "extracted": {
                    "name": None,
                    "phone": None,
                    "concern": "cancellation policy",
                    "preferred_day": None,
                    "preferred_time": None,
                    "language": "roman_urdu",
                },
                "handoff_required": True,
                "handoff_reason": "Policy confirmation needed",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            agent = ReceptionistAgent(
                groq=FakeGroq(responses),
                storage=JsonStorage(Path(tmp)),
                business_knowledge="Clinic information",
            )

            reply, alert = asyncio.run(agent.reply("123", "Cancellation policy kya hai?"))

            self.assertEqual(reply.lower().count("cancellation policy"), 1)
            self.assertNotIn("exact confirmation", reply.lower())
            self.assertIn("naam aur phone number", reply.lower())
            self.assertIsNotNone(alert)


if __name__ == "__main__":
    # Allows running this file directly with: python tests/test_agent.py
    unittest.main()
