"""Tests for WhatsApp webhook payload parsing."""

import unittest

from app.whatsapp_webhook import extract_text_messages


class WhatsAppWebhookTest(unittest.TestCase):
    def test_extract_text_messages(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "923001234567",
                                        "type": "text",
                                        "text": {"body": "Hello clinic"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        messages = extract_text_messages(payload)
        self.assertEqual(messages, [("923001234567", "Hello clinic")])

    def test_ignores_non_text_messages(self):
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {"from": "923001234567", "type": "image"},
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        self.assertEqual(extract_text_messages(payload), [])
