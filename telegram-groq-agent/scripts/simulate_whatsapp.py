#!/usr/bin/env python
"""Simulate WhatsApp messages locally — no Meta account required.

Modes:
  direct  Call ReceptionistAgent directly (fastest; needs Groq keys in .env)
  http    POST fake Meta payloads to a running webhook server

Examples:
  python scripts/simulate_whatsapp.py --mode direct --message "Clinic kahan hai?"
  python scripts/simulate_whatsapp.py --mode http --message "Salam"
  python scripts/simulate_whatsapp.py --mode http --scenarios
  python scripts/simulate_whatsapp.py --mode direct --booking
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

# Allow running as: python scripts/simulate_whatsapp.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bootstrap import create_receptionist_agent, load_business_config
from app.whatsapp_simulation import DEFAULT_SCENARIOS, build_meta_webhook_payload


BOOKING_SCRIPT = [
    "Appointment book karni hai acne ke liye",
    "Fatima Malik",
    "0312-5678901",
    "Active acne and dark marks",
    "Saturday",
    "2 PM",
]


async def run_direct(message: str, *, phone: str) -> None:
    config = load_business_config()
    agent = create_receptionist_agent(business_config=config)
    agent.channel = "whatsapp"
    chat_id = f"wa:{phone}"

    print(f"\n{'=' * 60}")
    print(f"Business: {config.business_name}")
    print(f"Mode:     direct (no Meta, no HTTP server)")
    print(f"{'=' * 60}")
    print(f"\nUSER: {message}")

    reply, staff_summary = await agent.reply(chat_id, message)
    print(f"\nAGENT:\n{reply}")

    if staff_summary:
        print(f"\nSTAFF ALERT:\n{staff_summary}")


async def run_direct_booking(*, phone: str) -> None:
    config = load_business_config()
    agent = create_receptionist_agent(business_config=config)
    agent.channel = "whatsapp"
    chat_id = f"wa:{phone}"
    agent.reset(chat_id)

    print(f"\n{'=' * 60}")
    print("Booking flow simulation (direct mode)")
    print(f"{'=' * 60}")

    for step, message in enumerate(BOOKING_SCRIPT, start=1):
        print(f"\n--- Step {step} ---")
        print(f"USER: {message}")
        reply, staff_summary = await agent.reply(chat_id, message)
        print(f"AGENT:\n{reply}")
        if staff_summary:
            print(f"STAFF ALERT:\n{staff_summary}")


async def run_http(
    message: str,
    *,
    phone: str,
    base_url: str,
    verify_token: str,
) -> None:
    payload = build_meta_webhook_payload(phone, message)
    webhook_url = f"{base_url.rstrip('/')}/webhook"

    print(f"\n{'=' * 60}")
    print(f"Mode:     http → {webhook_url}")
    print(f"Phone:    {phone}")
    print(f"{'=' * 60}")
    print(f"\nUSER: {message}")

    async with httpx.AsyncClient(timeout=60) as client:
        health = await client.get(base_url.rstrip("/") + "/")
        health.raise_for_status()
        info = health.json()
        print(f"\nServer:   {info.get('business')} (simulation={info.get('simulation_mode')})")

        if info.get("simulation_mode") != "true":
            print(
                "\nWARNING: Server is NOT in simulation mode. "
                "Set WHATSAPP_SIMULATION_MODE=true in .env and restart the server."
            )

        response = await client.post(webhook_url, json=payload)
        response.raise_for_status()
        body = response.json()

    replies = (body.get("simulated_replies") or {}).get(phone) or []
    if replies:
        print(f"\nAGENT:\n{replies[-1]}")
    else:
        print(f"\nResponse: {json.dumps(body, indent=2)}")
        if not replies:
            print("\nNo simulated_replies returned. Is WHATSAPP_SIMULATION_MODE=true on the server?")


async def run_http_scenarios(*, phone: str, base_url: str) -> None:
    print(f"\nRunning {len(DEFAULT_SCENARIOS)} scenarios against {base_url}\n")
    passed = 0
    for message, label in DEFAULT_SCENARIOS:
        print(f"--- {label} ---")
        try:
            await run_http(message, phone=phone, base_url=base_url, verify_token="")
            passed += 1
        except Exception as exc:
            print(f"FAILED: {exc}")
        print()
    print(f"Completed {passed}/{len(DEFAULT_SCENARIOS)} scenarios")


async def verify_webhook(base_url: str, verify_token: str) -> None:
    url = f"{base_url.rstrip('/')}/webhook"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            url,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": verify_token,
                "hub.challenge": "test-challenge-123",
            },
        )
    print(f"Verify status: {response.status_code}")
    print(f"Challenge:     {response.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate WhatsApp messages locally")
    parser.add_argument(
        "--mode",
        choices=["direct", "http"],
        default="http",
        help="direct = agent only; http = POST to webhook server",
    )
    parser.add_argument("--message", "-m", default="Clinic kahan hai phase 7 mein?")
    parser.add_argument("--phone", default="923001234567", help="Simulated sender phone (E.164, no +)")
    parser.add_argument("--url", default="http://localhost:8000", help="Webhook server base URL (http mode)")
    parser.add_argument("--verify-token", default="business-agent-verify")
    parser.add_argument("--scenarios", action="store_true", help="Run built-in test scenarios (http mode)")
    parser.add_argument("--booking", action="store_true", help="Run full booking script (direct mode)")
    parser.add_argument("--verify", action="store_true", help="Test Meta webhook verification handshake")
    args = parser.parse_args()

    if args.verify:
        asyncio.run(verify_webhook(args.url, args.verify_token))
        return

    if args.mode == "direct" and args.booking:
        asyncio.run(run_direct_booking(phone=args.phone))
        return

    if args.mode == "direct":
        asyncio.run(run_direct(args.message, phone=args.phone))
        return

    if args.scenarios:
        asyncio.run(run_http_scenarios(phone=args.phone, base_url=args.url))
        return

    asyncio.run(
        run_http(
            args.message,
            phone=args.phone,
            base_url=args.url,
            verify_token=args.verify_token,
        )
    )


if __name__ == "__main__":
    main()
