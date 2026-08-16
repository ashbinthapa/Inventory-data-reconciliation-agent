from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Stub Live Inventory API")

INVENTORY = {
    "SKU-1001": {"quantity": 110, "updated_at": "2026-08-15T08:30:00Z", "operator": "cycle_count"},
    "SKU-1002": {"quantity": 50, "updated_at": "2026-08-14T12:00:00Z", "operator": "manual_adjustment"},
    "SKU-1003": {"quantity": 12, "updated_at": "2026-08-15T08:45:00Z", "operator": "cycle_count"},
}

class InventoryRecord(BaseModel):
    sku: str
    quantity: int
    updated_at: str
    operator: str

@app.get("/inventory/{sku}", response_model=InventoryRecord)
def get_inventory(sku: str) -> InventoryRecord:
    if sku not in INVENTORY:
        raise HTTPException(status_code=404, detail="Unknown SKU")
    return InventoryRecord(sku=sku, **INVENTORY[sku])

@app.put("/inventory/{sku}", response_model=InventoryRecord)
def update_inventory(sku: str, quantity: int) -> InventoryRecord:
    if sku not in INVENTORY:
        raise HTTPException(status_code=404, detail="Unknown SKU")
    INVENTORY[sku]["quantity"] = quantity
    INVENTORY[sku]["updated_at"] = datetime.now(timezone.utc).isoformat()
    INVENTORY[sku]["operator"] = "reconciliation_agent"
    return InventoryRecord(sku=sku, **INVENTORY[sku])
