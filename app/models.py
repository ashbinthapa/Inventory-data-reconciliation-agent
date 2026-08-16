from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

SourceName = Literal["inventory", "warehouse"]
Action = Literal["AUTO_CORRECT", "MANUAL_REVIEW", "ESCALATE", "NO_ACTION"]

@dataclass
class Record:
    sku: str
    quantity: int
    updated_at: datetime
    metadata: dict

@dataclass
class Evidence:
    freshness: float
    historical_accuracy: float
    transaction_corroboration: float
    metadata_confidence: float

@dataclass
class SourceScore:
    source: SourceName
    evidence: Evidence
    weighted_score: float

@dataclass
class Decision:
    sku: str
    inventory_quantity: int
    warehouse_quantity: int
    ranking: list[SourceScore]
    winning_source: SourceName | None
    confidence_gap: float
    discrepancy_pct: float
    action: Action
    reasoning: list[str] = field(default_factory=list)
