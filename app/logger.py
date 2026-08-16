import json
from dataclasses import asdict
from pathlib import Path

LOG = Path(__file__).resolve().parents[1] / "decision_log.jsonl"


def log_decision(decision) -> None:
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(decision), default=str) + "\n")
