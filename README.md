# Profile-Guided Multi-Workflow Resource Orchestration Platform

Senior capstone project — team of 5, advised by Prof. Tossaphol.

**Start here:** [`CLAUDE.md`](CLAUDE.md) is the working summary and the guardrails.
[`docs/System_Architecture_v2.md`](docs/System_Architecture_v2.md) is the full design
reference; [`docs/PoC_and_Validation_Plan.md`](docs/PoC_and_Validation_Plan.md) is what
September is for. If code and a document disagree, the document is not automatically right —
flag the mismatch and resolve it explicitly, don't silently follow either one.

## What this project is

A system that receives multiple workflows, each a DAG, and — for the whole batch at once,
offline — decides **which model profile serves each task** and **how many instances of each
profile to provision**, minimising provisioning cost under a fixed GPU budget.

Two decisions, coupled. Routing determines load; load determines instance counts; instance
counts consume the budget; a binding budget constrains routing. Formally it is a **modular
capacitated facility location problem with a budget constraint** — see
`docs/System_Architecture_v2.md` §1.8, which is what justifies the algorithm choices.

## What the repo currently is

A proof-of-concept, and only that. It exists to answer four questions before the real system
is built, and it is **not** a scaled-down version of the system — no registry, no profiling,
no execution, no domain data.

| Test | Question | Owner |
|---|---|---|
| T1 | Which constraint should Track B relax, and does its bound beat the LP bound? | 075 |
| T2 | Can greedy construction be defeated by aggregate coupling? | 035 |
| T3 | Over what budget range does the problem have interesting structure? | 089 |
| T4 | Is Track A worth its complexity relative to Track C? | 035 + 089 |

**Deadline: 30 September 2026**, coinciding with milestone M1.

A *negative* answer to any of these is a success. "Track B provides no bound advantage" is a
finding that saves a semester. The PoC fails only if the questions remain open.

## Repo layout

```
CLAUDE.md                 Working summary + guardrails. Read first
docs/
  System_Architecture_v2.md   Authoritative design reference
  PoC_and_Validation_Plan.md  Scope, deliverables, schedule, risks
  research_papers/            Literature tracking, feeds Ch.2
  v1_superseded/              Retired v1 design. Not current — see its README
poc/
  formulation/            Types (§5.1) and the I1-I5 invariant checks
  instances/              Synthetic generator + hand-verified fixtures
  core/                   ProvisioningState and the shared decision rule
  tracks/                 exact_milp, track_c_lp, track_b_lagr, track_a_greedy
  harness/                Matched-condition runner and metrics
  tests/
data/                     LogHub samples + prepared batches — Semester 2, not PoC scope
scripts/                  Data prep
```

`poc/` is currently a documented skeleton. Every module carries its spec reference, build
step, and owner; the algorithm bodies raise `NotImplementedError` until built in order.

## Build order

Do not reorder — each step is verifiable before the next, and **the exact solver comes before
any heuristic** because nothing else can be checked for correctness without ground truth.

| # | Build | Verify by |
|---|---|---|
| 1 | `formulation/types.py` | Types instantiate |
| 2 | `formulation/invariants.py` | Hand-built valid and violating results |
| 3 | `instances/generator.py` | Instances well-formed; every `C(t)` non-empty |
| 4 | `tracks/exact_milp.py` | **Returns 280 on `adversarial_3t2p`** |
| 5 | `core/provisioning.py` | admit/release/snapshot/restore; budget rejection |
| 6 | `core/decision_rule.py` | Known pools, known picks; all-infeasible returns None |
| 7 | `tracks/track_c_lp.py` | Bound ≤ MILP optimum; satisfies I1-I5 |
| 8 | `tracks/track_b_lagr.py` | Bound ≤ optimum; compare to LP bound (T1) |
| 9 | `tracks/track_a_greedy.py` | Satisfies I1-I5; **returns 300 on `adversarial_3t2p`** |
| 10 | `harness/` | Reproduces a known result end-to-end |

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "import pulp; print(pulp.listSolvers(onlyAvailable=True))"   # expect PULP_CBC_CMD
pytest poc/tests
```

## Scope guard

> If a module does not help answer T1, T2, T3 or T4, it does not belong in the PoC.

Not built, deliberately: Executor Registry, Profiling Subsystem, Execution Engine, drift
detection and re-optimisation, Zookeeper/LogHub domain data, monitoring, fallback, framework
integration, and Track A's relocate/consolidate/elaborate multi-start. Full list in
`CLAUDE.md`.

## Settled — do not reintroduce

- **HEFT is not used.** Neither source paper has precedence constraints or a makespan term,
  so upward rank orders tasks by a quantity absent from the objective. This was a real error
  in the v1 design.
- **Capacity is consumed by instances, not by task assignments.** v1 had a slot ledger
  decremented per task. Tasks add *load*; load may or may not force a new instance.
- **Precedence does not enter the optimisation.** DAG edges determine execution order only.

## Team

| ID | PoC responsibility | Owns |
|---|---|---|
| 035 | Greedy construction, T2, T4 | Track A |
| 075 | Formulation draft, Lagrangian, Track C, T1 | Track B |
| 077 | PoC report, results write-up | Phase C, deferred to Sem 2 |
| 083 | Instance generator, repo, architecture update | Infrastructure |
| 089 | MILP reference, T3, T4 support | Evaluation |
