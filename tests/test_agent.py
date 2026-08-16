from app.agent import reconcile


def test_demo_case_detects_conflict_and_auto_corrects():
    decision = reconcile("SKU-1002")
    assert decision.inventory_quantity == 50
    assert decision.warehouse_quantity == 60
    assert decision.winning_source == "warehouse"
    assert decision.action == "AUTO_CORRECT"
