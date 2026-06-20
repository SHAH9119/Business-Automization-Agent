import unittest
from pathlib import Path

from app.knowledge import SectionRetriever, load_section_retriever

PACK_DIR = Path(__file__).resolve().parents[2] / "royce-aesthetics-agent"

class SectionRetrieverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = load_section_retriever(PACK_DIR)

    def test_session_status_collecting_appointment_loads_only_booking(self):
        """When actively collecting appointment details and no other topic matched, only load booking flow to save tokens."""
        # A simple response like "Ali" or "Tuesday" shouldn't load FAQ + services
        result = self.retriever("Ali", session_status="collecting_appointment")
        self.assertIn("clinic_profile.md", result)
        self.assertIn("booking_flow.md", result)
        self.assertNotIn("services.md", result)
        self.assertNotIn("prices.md", result)
        self.assertNotIn("faq.md", result)

    def test_explicit_topic_overrides_collecting_appointment(self):
        """When actively collecting appointment details, an explicit question (like price) should load the specific topic."""
        # Use a phrase that only triggers price, not service (avoids 'what is')
        result = self.retriever("How much does it cost?", session_status="collecting_appointment")
        self.assertIn("prices.md", result)
        self.assertNotIn("booking_flow.md", result)
        self.assertNotIn("services.md", result)

    def test_cancellation_question_loads_faq_not_booking(self):
        """Questions about cancellation during booking should load FAQ and not fallback to booking."""
        result = self.retriever("Can I cancel my appointment?", session_status="collecting_appointment")
        self.assertIn("faq.md", result)
        self.assertNotIn("booking_flow.md", result)
        self.assertNotIn("services.md", result)

    def test_rescheduling_question_loads_faq_not_booking(self):
        """Rescheduling policy questions should not restart appointment collection."""
        result = self.retriever(
            "I want to reschedule my appointment",
            session_status="collecting_appointment",
        )
        self.assertIn("faq.md", result)
        self.assertNotIn("booking_flow.md", result)

    def test_open_pores_question_loads_services_not_faq(self):
        """The word 'open' in a condition must not be mistaken for clinic hours."""
        result = self.retriever("What treatment do you have for open pores?")
        self.assertIn("services.md", result)
        self.assertNotIn("faq.md", result)

    def test_opening_hours_question_loads_faq(self):
        """A real opening-hours question should still load the FAQ."""
        result = self.retriever("What time do you open?")
        self.assertIn("faq.md", result)
        self.assertNotIn("services.md", result)

    def test_mixed_topic_keeps_strict_budget(self):
        """If a user asks for both price and service ('What is the price of HIFU?'), 
        we prioritize price and drop the massive services.md to stay under the token limit."""
        result = self.retriever("What is the price of HIFU?")
        self.assertIn("prices.md", result)
        self.assertNotIn("services.md", result)

    def test_word_boundary_matching(self):
        """Substring matching shouldn't cause false positives. 'fee' in 'feel' shouldn't trigger price."""
        result = self.retriever("I feel redness after treatment")
        # Should not load price based on 'feel'
        self.assertNotIn("prices.md", result)
        # It has 'treatment' so it should load services
        self.assertIn("services.md", result)

    def test_roman_urdu_price_triggers(self):
        """Roman Urdu price questions should trigger prices.md"""
        triggers = ["qeemat", "kharcha", "kitne", "daam", "paisay"]
        for trigger in triggers:
            with self.subTest(trigger=trigger):
                result = self.retriever(f"Leg laser ka {trigger} kya hai?")
                self.assertIn("prices.md", result)

    def test_handoff_trigger(self):
        """Urgent medical keywords or explicit requests for staff should trigger handoff_flow.md"""
        triggers = ["I have an emergency", "severe pain in my arm", "I want to speak to a doctor", "staff se baat karni hai"]
        for trigger in triggers:
            with self.subTest(trigger=trigger):
                result = self.retriever(trigger)
                self.assertIn("handoff_flow.md", result)
                self.assertIn("safety_rules.md", result)

    def test_urgent_service_message_prioritizes_handoff(self):
        """Urgent symptoms should not load general treatment descriptions."""
        result = self.retriever("I have severe pain after my HIFU treatment")
        self.assertIn("handoff_flow.md", result)
        self.assertIn("safety_rules.md", result)
        self.assertNotIn("services.md", result)
        self.assertNotIn("prices.md", result)

    def test_fallback_loads_only_faq(self):
        """A generic message that matches nothing should load only FAQ, not FAQ+services to save tokens."""
        result = self.retriever("Hello")
        self.assertIn("faq.md", result)
        self.assertNotIn("services.md", result)
        self.assertNotIn("prices.md", result)
        self.assertNotIn("booking_flow.md", result)

    def test_service_name_questions_load_services(self):
        """Questions like 'what is HIFU' should load services.md."""
        result = self.retriever("What is HIFU?")
        self.assertIn("services.md", result)

    def test_route_token_budget(self):
        """Ensure the returned text lengths stay under strict budget.
        1 token is roughly 4 characters. We need to leave headroom for:
        - System prompt (rules)
        - Conversation history (up to 8 messages)
        - Session profile JSON
        - Model output (up to 900 tokens)
        So we enforce a strict 18,000 char (~4,500 token) limit for the knowledge text itself,
        leaving ~1,500 tokens of headroom for the rest of the 6K TPM limit.
        """
        STRICT_BUDGET = 16000

        fallback = self.retriever("Hello")
        self.assertLess(len(fallback), STRICT_BUDGET, "Fallback route is too heavy")

        # Booking route: profile + booking flow.
        booking = self.retriever("Ali", session_status="collecting_appointment")
        self.assertLess(len(booking), STRICT_BUDGET, "Booking route is too heavy")

        # Price route: profile + prices.
        price = self.retriever("How much does it cost?")
        self.assertLess(len(price), STRICT_BUDGET, "Price route is too heavy")

        # Mixed topic: Price + Service request should drop service.
        mixed = self.retriever("What is the price of HIFU?")
        self.assertLess(len(mixed), STRICT_BUDGET, "Mixed topic route is too heavy")

        cancellation = self.retriever(
            "Can I cancel my appointment?",
            session_status="collecting_appointment",
        )
        self.assertLess(len(cancellation), STRICT_BUDGET, "Cancellation route is too heavy")

        # Service route is the largest normal route.
        service = self.retriever("What is HIFU?")
        self.assertLess(len(service), STRICT_BUDGET, "Service route is too heavy")

        urgent = self.retriever("I have severe pain after my HIFU treatment")
        self.assertLess(len(urgent), STRICT_BUDGET, "Urgent route is too heavy")

if __name__ == "__main__":
    unittest.main()
