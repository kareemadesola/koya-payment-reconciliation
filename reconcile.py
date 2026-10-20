#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.
Run:  python3 reconcile.py

Rules (see README):
  - Unreadable lines and events without a txn_id are ignored.
  - A payment can be attempted several times under the same txn_id;
    only the latest attempt (by ts) counts.
  - A payment is collected only if its latest attempt is "success".
"""
import json
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Amounts arrive as numbers or as strings like "4,804.15"."""
    if isinstance(value, str):
        value = value.replace(",", "").strip()
    return Decimal(str(value))


def parse_ts(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


latest = {}  # txn_id -> (ts, event)

with open("payments.jsonl", encoding="utf-8") as f:
    for line in f:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        txn_id = event.get("txn_id")
        if not txn_id:
            continue
        ts = parse_ts(event["ts"])
        # ">=" keeps the later line in the file if two attempts share a ts
        if txn_id not in latest or ts >= latest[txn_id][0]:
            latest[txn_id] = (ts, event)

total = Decimal("0")
count = 0
for _, event in latest.values():
    if event["status"] == "success":
        total += parse_amount(event["amount"])
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{int(total.quantize(Decimal('1'), rounding=ROUND_HALF_UP))}")
