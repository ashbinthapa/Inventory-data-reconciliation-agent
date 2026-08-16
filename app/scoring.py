from __future__ import annotations

from statistics import mean

from .models import Evidence, Record, SourceName, SourceScore

WEIGHTS = {
    "freshness": 0.30,
    "historical_accuracy": 0.30,
    "transaction_corroboration": 0.25,
    "metadata_confidence": 0.15,
}


def freshness_score(record: Record, other: Record) -> float:
    # 100 means at least as fresh; lower values decay with the age difference.
    diff_hours = abs((record.updated_at - other.updated_at).total_seconds()) / 3600
    if record.updated_at >= other.updated_at:
        return 100.0
    return max(0.0, 100.0 - diff_hours * 4.0)


def historical_accuracy_score(source: SourceName, sku: str, history: list[dict]) -> float:
    rows = [r for r in history if r["sku"] == sku]
    if not rows:
        return 60.0
    errors = [float(r[f"{source}_abs_error"]) for r in rows]
    mean_error = mean(errors)
    return max(0.0, 100.0 - min(mean_error * 8.0, 100.0))


def transaction_corroboration_score(record: Record, transactions: list[dict], inventory_quantity: int) -> float:
    if not transactions:
        return 50.0
    net = 0
    for tx in transactions:
        qty = int(tx["quantity"])
        net += qty if tx["transaction_type"] == "RECEIPT" else -qty
    # Measure whether the transaction trail plausibly moves the live inventory toward this source.
    expected = inventory_quantity + net
    delta = abs(expected - record.quantity)
    return max(0.0, 100.0 - delta * 6.0)


def metadata_score(record: Record) -> float:
    score = 0.0
    metadata = record.metadata
    if metadata.get("warehouse_id"):
        score += 50
    if metadata.get("record_status") == "verified":
        score += 50
    if metadata.get("operator"):
        score += 50
    return min(score, 100.0)


def score_source(
    source: SourceName,
    record: Record,
    other: Record,
    sku: str,
    history: list[dict],
    transactions: list[dict],
    inventory_quantity: int,
) -> SourceScore:
    evidence = Evidence(
        freshness=freshness_score(record, other),
        historical_accuracy=historical_accuracy_score(source, sku, history),
        transaction_corroboration=transaction_corroboration_score(record, transactions, inventory_quantity),
        metadata_confidence=metadata_score(record),
    )
    score = (
        evidence.freshness * WEIGHTS["freshness"]
        + evidence.historical_accuracy * WEIGHTS["historical_accuracy"]
        + evidence.transaction_corroboration * WEIGHTS["transaction_corroboration"]
        + evidence.metadata_confidence * WEIGHTS["metadata_confidence"]
    )
    return SourceScore(source=source, evidence=evidence, weighted_score=round(score, 2))
