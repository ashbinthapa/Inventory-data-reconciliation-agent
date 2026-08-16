from datetime import datetime, timezone

from app.models import Record
from app.scoring import freshness_score, historical_accuracy_score


def test_newer_source_gets_full_freshness_score():
    now = datetime(2026, 8, 15, tzinfo=timezone.utc)
    old = Record("SKU", 1, now.replace(hour=8), {})
    new = Record("SKU", 1, now.replace(hour=9), {})
    assert freshness_score(new, old) == 100.0


def test_historical_accuracy_penalises_error():
    history = [{"sku": "SKU", "inventory_abs_error": "1", "warehouse_abs_error": "6"}]
    assert historical_accuracy_score("inventory", "SKU", history) > historical_accuracy_score("warehouse", "SKU", history)
