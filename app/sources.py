from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from .models import Record

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_warehouse() -> dict[str, Record]:
    rows = {}
    with open(DATA / "warehouse_weekly.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[r["sku"]] = Record(
                sku=r["sku"],
                quantity=int(r["quantity"]),
                updated_at=parse_dt(r["reported_at"]),
                metadata={"warehouse_id": r["warehouse_id"], "record_status": r["record_status"]},
            )
    return rows


def load_transactions(sku: str, since: datetime) -> list[dict]:
    results: list[dict] = []
    with open(DATA / "transaction_log.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["sku"] == sku and parse_dt(r["occurred_at"]) >= since:
                results.append(r)
    return results


def load_history() -> list[dict]:
    with open(DATA / "historical_reconciliations.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
