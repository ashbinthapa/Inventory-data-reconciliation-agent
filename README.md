# AI – Inventory Conflict Resolution Agent

A small, auditable agent that reconciles a live inventory system with a weekly warehouse feed. When the two sources disagree, it gathers contextual evidence, ranks source credibility, explains the ranking, and chooses a conservative action.

## Why this approach

The decision is intentionally **not** an LLM-only judgement. Stock reconciliation can trigger real operational consequences, so the core decision is deterministic and inspectable. The agent behaves like an orchestrator:

1. Query the live inventory API.
2. Load the latest warehouse report.
3. Detect SKU-level discrepancies.
4. Gather context: source freshness, historical accuracy, transaction evidence, and metadata confidence.
5. Score both sources using documented weights.
6. Log the evidence and reasoning before taking action.
7. Choose `AUTO_CORRECT`, `MANUAL_REVIEW`, or `ESCALATE`.

An LLM could be added later to summarise evidence for a human, but it would not be the final authority without strong safeguards.

## Credibility criteria

The agent scores each source from 0–100 using four criteria:

| Criterion | Weight | What it measures |
|---|---:|---|
| Freshness | 30% | How recently the source was updated relative to the other source |
| Historical accuracy | 30% | Agreement with previously resolved records |
| Transaction corroboration | 25% | Whether recent transactions support the reported level |
| Metadata confidence | 15% | Completeness/quality of timestamps, source IDs and record metadata |

Trade-off: freshness and historical accuracy dominate because a stale or historically unreliable source should rarely override a current, trusted source. Transaction corroboration is deliberately large enough to overturn freshness when the transaction trail strongly contradicts it. Metadata has lower weight because good metadata improves trust but does not prove the stock number is correct.

## Decision policy

After scoring, the agent calculates the confidence gap between the top-ranked source and the runner-up.

- `AUTO_CORRECT`: winning source score >= 75, confidence gap >= 15, and discrepancy <= 20% of the current inventory value.
- `MANUAL_REVIEW`: winning source score >= 65 but the automatic correction criteria are not met.
- `ESCALATE`: low absolute confidence (top score < 55), a large discrepancy (>50%), or nearly tied sources (gap < 8).

When the **warehouse feed** wins, `AUTO_CORRECT` updates the live inventory record to the warehouse quantity. When the **inventory system** wins, the agent does not blindly rewrite it; it records the warehouse value as stale/conflicting and recommends follow-up. This is safer than changing a live value just to make two systems agree.

## Demo scenario

The included data deliberately contains a real conflict for `SKU-1002`:

- Live inventory says **50** units.
- Warehouse weekly feed says **60** units.
- The warehouse report is newer, has stronger metadata, and historically agrees more often with reconciled stock counts.
- Recent transactions explain part of the difference but not all of it.

The agent should rank the warehouse source first and, because the discrepancy is moderate (20%) and confidence is high, choose `AUTO_CORRECT`.

## Run

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m app.agent
```

Optional API mode:

```bash
uvicorn app.inventory_api:app --reload
```

Then visit `http://127.0.0.1:8000/inventory/SKU-1002`.

## Tests

```bash
pytest -q
```

Note: `tests/test_agent.py` runs the real `reconcile()` flow, which mutates the in-memory `INVENTORY` dict when it auto-corrects. Run the suite in a fresh process (as `pytest` does by default) rather than re-invoking `reconcile("SKU-1002")` multiple times in the same session, or the "before" quantity will no longer be 50.

## Repository structure

```text
app/
  agent.py             # orchestration and decision policy
  inventory_api.py     # tiny stub of a live inventory API
  scoring.py           # credibility scoring
  models.py            # typed data models
  sources.py           # warehouse feed + transaction readers
  logger.py            # structured decision log

data/
  warehouse_weekly.csv
  transaction_log.csv
  historical_reconciliations.csv

tests/
  test_scoring.py
  test_agent.py
```

## What I would do next

With more time I would:

- replace the stub API and CSV reader with production connectors;
- persist decisions and overrides in a database;
- add idempotency and transactional writes around auto-correction;
- calibrate thresholds from real incident data instead of hand-picked demo values;
- monitor false corrections, review rates and source drift;
- add a human feedback loop so reviewer decisions improve historical-accuracy estimates;
- isolate test state so `test_agent.py` doesn't depend on `INVENTORY` being unmutated (e.g. reset the dict in a fixture, or inject inventory state instead of importing a module-level global);
- add an LLM only for evidence summarisation / operator explanations, with the deterministic policy remaining the gatekeeper.
