# Profile-Guided Multi-Workflow Resource Orchestration Platform

Senior capstone project — team of 5, advised by Prof. Tossaphol.

**Start here:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) is the authoritative design
reference. Everything in this repo should be consistent with it; if code and that document
disagree, the document is not automatically right — flag the mismatch and resolve it
explicitly, don't silently follow either one.

## What this project is

A system that receives multiple workflows, each a DAG, and — for the whole batch at once,
offline — decides which model/hardware/config each task should use, using real measured
performance data, accounting for the fact that every workflow shares one real, limited
resource pool. Built on top of Murakkab (Chaudhry et al., OSDI '26), replacing its exact
MILP solver with two faster, non-exact multi-workflow algorithms (HEFT and Lagrangian
relaxation) for direct comparison.

## Repo layout

```
docs/                    Architecture, schedule, and full paper research (source of truth)
phase_a/                 DAG ingestion + Layer 1 eligibility lookup
phase_b/heft/             Track A — HEFT multi-workflow allocator
phase_b/lagrangian/       Track B — Lagrangian relaxation allocator
phase_c/                 Execution, measurement, profiling, drift detection
registry/                Executor registry (manual registration, Murakkab's 3-field schema)
data/                    Real log samples (LogHub) + prepared evaluation batches
scripts/                 Data prep, offline baselines (free MILP solver via PuLP/CBC)
tests/                   Unit + regression tests, keyed to Architecture_Design.md's worked examples
```

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

See `docs/SCHEDULE.md` for the current stage and priority. As of this repo's creation:
**Phase B (the multi-workflow optimizer) is the primary active focus** — see
`docs/ARCHITECTURE.md`'s "Development Priority" section for the full reasoning behind that
and everything else currently in or out of scope.

## Team

| ID | Role | Owns |
|---|---|---|
| 035 | Phase A / HEFT Track Lead | Layer 1, HEFT (Phase B Track A) |
| 075 | Phase B / Lagrangian Track Lead | Inner decision rule, Lagrangian relaxation (Track B) |
| 077 | Phase C Lead | Measurement, profiling, drift detection |
| 083 | Infrastructure & Integration Lead | Registry, shared ledger, wiring, testing |
| 089 | Evaluation & Documentation Lead | Baselines, statistics, write-up |
