"""Regression tests for services, prices, and common customer wording."""

import unittest
from pathlib import Path

from app.catalog import ServiceCatalog


CATALOG_PATH = (
    Path(__file__).resolve().parents[2]
    / "royce-aesthetics-agent"
    / "config"
    / "service_catalog.json"
)


class ServiceCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = ServiceCatalog.from_file(CATALOG_PATH)

    def test_every_public_offering_can_be_found(self):
        """Every public service/condition must work with at least its first alias."""
        for item in self.catalog.public:
            with self.subTest(service=item["name"]):
                result = self.catalog.evaluate(f"Do you provide {item['aliases'][0]}?")
                self.assertIsNotNone(result)
                self.assertFalse(result["handoff_required"])
                self.assertIn("available", result["reply"].lower())

    def test_every_demo_price_can_be_found(self):
        """Every demo-priced item must return its configured demo price."""
        for item in self.catalog.demo:
            with self.subTest(service=item["name"]):
                result = self.catalog.evaluate(f"What is the price of {item['aliases'][0]}?")
                self.assertIsNotNone(result)
                self.assertIn(item["demo_price"].lower(), result["reply"].lower())
                self.assertIn("final price may vary", result["reply"].lower())
                self.assertNotIn("not an official", result["reply"].lower())
                self.assertNotIn("demo estimate", result["reply"].lower())

    def test_hydrafacial_is_marked_demo_only(self):
        result = self.catalog.evaluate("Hydrafacial waghera hota hai and what is the price?")
        self.assertIn("available", result["reply"].lower())
        self.assertIn("pkr 8,000", result["reply"].lower())

    def test_full_body_laser_maps_to_laser_hair_removal(self):
        result = self.catalog.evaluate("What's the price of full body laser per session?")
        self.assertIn("laser hair removal", result["reply"].lower())
        self.assertIn("pkr 5,000", result["reply"].lower())

    def test_mole_removal_has_demo_price(self):
        result = self.catalog.evaluate("Can you remove a mole and how much does it cost?")
        self.assertIn("mole", result["reply"].lower())
        self.assertIn("pkr 5,000", result["reply"].lower())

    def test_waxing_is_not_claimed_as_available(self):
        result = self.catalog.evaluate("Do you do full body waxing and what is the price?")
        self.assertTrue(result["handoff_required"])
        self.assertIn("not listed", result["reply"].lower())

    def test_service_list_question_returns_summary(self):
        result = self.catalog.evaluate("Tell me what services you offer")
        self.assertIn("hair transplant", result["reply"].lower())
        self.assertIn("laser hair removal", result["reply"].lower())
        self.assertIn("\n- ", result["reply"])

    def test_roman_urdu_is_used_only_when_requested(self):
        english = self.catalog.evaluate("What is the price of hydrafacial?", roman_urdu=False)
        roman = self.catalog.evaluate("Hydrafacial ki price kya hai?", roman_urdu=True)

        self.assertIn("the estimated price", english["reply"].lower())
        self.assertNotIn("available hai", english["reply"].lower())
        self.assertIn("available hai", roman["reply"].lower())
        self.assertIn("price", roman["reply"].lower())


if __name__ == "__main__":
    unittest.main()
