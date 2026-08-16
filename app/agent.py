from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .inventory_api import INVENTORY
from .logger import log_decision
from .models import Decision, Record
from .scoring import score_source
from .sources import load_history, load_transactions, load_warehouse


def inventory_record(sku: str) -> Record:
    raw = INVENTORY[sku]
    return Record(
        sku=sku,
        quantity=raw["quantity"],
        updated_at=datetime.fromisoformat(raw["updated_at"].replace("Z", "+00:00")),
        metadata={"operator": raw["operator"]},
    )


def reconcile(sku: str) -> Decision:
    print(f"\\n[1] Query live inventory system: {sku}")
    inv = inventory_record(sku)
    print(f"    inventory={inv.quantity}, updated={inv.updated_at.isoformat()}")

    print("[2] Fetch latest warehouse report")
    warehouse = load_warehouse()[sku]
    print(f"    warehouse={warehouse.quantity}, reported={warehouse.updated_at.isoformat()}")

    if inv.quantity == warehouse.quantity:
        decision = Decision(sku, inv.quantity, warehouse.quantity, [], None, 0.0, 0.0, "NO_ACTION", ["Sources agree."])
        log_decision(decision)
        print("[3] No discrepancy")
        return decision

    print("[3] Discrepancy detected")
    history = load_history()
    since = min(inv.updated_at, warehouse.updated_at) - timedelta(hours=2)
    transactions = load_transactions(sku, since)
    print(f"    recent transactions considered: {len(transactions)}")

    inv_score = score_source("inventory", inv, warehouse, sku, history, transactions, inv.quantity)
    wh_score = score_source("warehouse", warehouse, inv, sku, history, transactions, inv.quantity)
    ranking = sorted([inv_score, wh_score], key=lambda x: x.weighted_score, reverse=True)

    winner = ranking[0].source
    gap = round(ranking[0].weighted_score - ranking[1].weighted_score, 2)
    discrepancy_pct = round(abs(inv.quantity - warehouse.quantity) / max(inv.quantity, 1) * 100, 2)

    reasoning = [
        f"Freshness: inventory={inv_score.evidence.freshness:.1f}, warehouse={wh_score.evidence.freshness:.1f}.",
        f"Historical accuracy: inventory={inv_score.evidence.historical_accuracy:.1f}, warehouse={wh_score.evidence.historical_accuracy:.1f}.",
        f"Transaction corroboration: inventory={inv_score.evidence.transaction_corroboration:.1f}, warehouse={wh_score.evidence.transaction_corroboration:.1f}.",
        f"Metadata confidence: inventory={inv_score.evidence.metadata_confidence:.1f}, warehouse={wh_score.evidence.metadata_confidence:.1f}.",
        f"Weighted ranking: {ranking[0].source} {ranking[0].weighted_score:.2f} vs {ranking[1].source} {ranking[1].weighted_score:.2f}; gap={gap:.2f}.",
    ]

    if discrepancy_pct > 50 or gap < 8 or ranking[0].weighted_score < 55:
        action = "ESCALATE"
    elif ranking[0].weighted_score >= 75 and gap >= 15 and discrepancy_pct <= 20 and winner == "warehouse":
        action = "AUTO_CORRECT"
    else:
        action = "MANUAL_REVIEW"

    reasoning.append(f"Policy result: {action}.")
    if action == "AUTO_CORRECT":
        reasoning.append(f"Planned correction: change inventory from {inv.quantity} to {warehouse.quantity} because warehouse ranked first with high confidence.")
    elif winner == "inventory":
        reasoning.append("Live inventory remains unchanged; the warehouse report is treated as the conflicting source.")

    decision = Decision(
        sku=sku,
        inventory_quantity=inv.quantity,
        warehouse_quantity=warehouse.quantity,
        ranking=ranking,
        winning_source=winner,
        confidence_gap=gap,
        discrepancy_pct=discrepancy_pct,
        action=action,
        reasoning=reasoning,
    )
    # Audit the judgement before any state-changing action.
    log_decision(decision)

    if action == "AUTO_CORRECT":
        INVENTORY[sku]["quantity"] = warehouse.quantity
        INVENTORY[sku]["operator"] = "reconciliation_agent"
        # Record the post-action state as a second audit event.
        decision.reasoning.append(f"Applied correction: live inventory is now {warehouse.quantity}.")
        log_decision(decision)

    return decision


def print_decision(decision: Decision) -> None:
    print("\\n[4] Credibility ranking")
    for item in decision.ranking:
        print(f"    {item.source:9s} -> {item.weighted_score:6.2f}")
    print("[5] Reasoning")
    for line in decision.reasoning:
        print(f"    - {line}")
    print(f"[6] FINAL DECISION: {decision.action}")


if __name__ == "__main__":
    decision = reconcile("SKU-1002")
    print_decision(decision)
