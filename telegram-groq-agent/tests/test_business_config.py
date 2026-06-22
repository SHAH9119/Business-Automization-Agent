"""Tests for business config loading."""

import json
import tempfile
import unittest
from pathlib import Path

from app.business_config import BusinessConfig


class BusinessConfigTest(unittest.TestCase):
    def test_loads_greeting_from_agent_config(self):
        data = {
            "business_name": "Test Clinic",
            "brand_name": "Test Brand",
            "contact": {"phone": "0300-1111111"},
            "location": {"area": "Phase 7", "city": "Rawalpindi"},
            "hours": {"open": "10:00 AM", "close": "06:00 PM", "days": "Mon-Sat"},
            "agent_persona": {
                "greeting_en": "Custom English greeting",
                "greeting_ur": "Custom Urdu greeting",
            },
            "escalation_keywords": ["custom urgent"],
        }
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            config_dir = pack / "config"
            config_dir.mkdir()
            (config_dir / "agent_config.json").write_text(json.dumps(data), encoding="utf-8")

            config = BusinessConfig.from_pack_dir(pack)

        self.assertEqual(config.business_name, "Test Clinic")
        self.assertEqual(config.phone, "0300-1111111")
        self.assertEqual(config.greeting_en, "Custom English greeting")
        self.assertEqual(config.greeting_ur, "Custom Urdu greeting")
        self.assertIn("custom urgent", config.escalation_keywords)
        self.assertIn("10:00 AM", config.preferred_time_prompt())

    def test_defaults_when_config_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = BusinessConfig.from_pack_dir(Path(tmp))
        self.assertEqual(config.business_name, "the clinic")
        self.assertEqual(config.hours_open, "12:00 PM")
