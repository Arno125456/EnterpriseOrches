# Repository guide — every file, explained

**What this is.** A file-by-file map of the whole repository. If you have just been handed
this repo and do not know what any of it is, read
[`ORIENTATION.md`](ORIENTATION.md) first for *what the project is*, then use this for *where
things are*.

Every file is listed. Nothing is hidden in an "etc."

---

## The 60-second map

```
EnterpriseOrches/
├── docs/           what we know, decided, measured and are writing   ← start here
├── poc/            the proof-of-concept. THE code that matters
├── prototype/      the closed loop, against a simulated executor
├── scripts/        one-off audits and table generators, each reproducing a finding
├── data/           input batches for the multi-workflow experiments
└── *.md            project-level state: plan, handoff, guardrails
```

**If you only open one directory, open `poc/`.** It is the PoC, it is fully tested, and it is
what the four research questions were answered with. `prototype/` is explicitly outside PoC
scope.

---

## Root — project state

These are the files that say *where the project is*, as opposed to how it works.

| File | Lines | What it is |
|---|---|---|
| **`README.md`** | 187 | Front door. Routes you by role. Points here and to `ORIENTATION.md` |
| **`CLAUDE.md`** | 255 | **The guardrails.** Working summary, the ground-truth fixture, the build order, the invariants, the scope guard ("do not build") and the settled decisions that must not be reintroduced. **Read before changing code** |
| **`PLAN.md`** | 192 | Eight steps from today to the M1 presentation on 30 Sep. No options, no parallel tracks. Also holds the Semester 2 parked list |
| **`HANDOFF.md`** | 206 | State and decisions already taken, the open-question table, and the **do-not-quote** list. What you would read to take over the project |
| **`PROGRESS.md`** | 190 | Milestone tracking and deliverable status. `mickie`-origin, more formal in tone |
| **`BRANCHES.md`** | 136 | **Read before merging anything.** How the two branches diverged and what reconciling them costs |
| `requirements.txt` | 13 | `pulp`, `numpy`, `pytest`. CBC ships with PuLP |
| `pytest.ini` | 5 | Test discovery config |
| `.gitignore` | 20 | |

---

## `docs/` — grouped by what you are trying to do

### Top level

| File | Lines | What it is |
|---|---|---|
| **`ORIENTATION.md`** | 494 | **Start here if you are new.** The whole project in one file — problem, design, formal model, the fixture, findings, evidence discipline, open items. Assumes nothing |
| `README.md` | 121 | Documentation index. Find your row |
| `REPO_GUIDE.md` | — | This file |

### `docs/design/` — how the system is built

| File | Lines | What it is |
|---|---|---|
| **`System_Architecture_v2.md`** | 908 | **The design of record.** §1 is the formulation you ratify at T0; §1.7 is where the coupling lives; §1.8 identifies the problem class; §2 principles and components; §3 jobs J1–J10; §4 component architecture; §5 detailed design including all three track algorithms; §8 traceability; §9 the reference map. **Amended nine times by measurement — every amendment is marked in place** |
| `component_reference.md` | 351 | What each component *does*, what it must *become*, and whether it earns its place. Written as behaves / does / fits / becomes |
| `pipeline.md` | 289 | ASCII diagrams of the end-to-end PoC pipeline — instance construction, invariant gating, track execution, metric aggregation |

### `docs/evidence/` — what we actually measured

| File | Lines | What it is |
|---|---|---|
| **`poc_findings_summary.md`** | 230 | **What we believe now, at what confidence** — plus the *"numbers that were corrected"* table. **Check this before quoting any number anywhere** |
| `poc_findings.md` | 2299 | The full chronological log, 35 findings **including superseded ones**. History is kept deliberately: F14 was corrected by F15 then F16, F16's speedup by F29, F34's headline by F35. Do not quote from it without checking the summary first |
| `chapter3_benchmark_results.md` | 143 | Scale benchmark tables and their LaTeX, ready for Chapter 3. Its §1 summary was corrected by F32 |

### `docs/proposal/` — what we are writing

| File | Lines | What it is |
|---|---|---|
| `proposal_narrative.md` | 161 | **The argument chain** that makes the findings one story, and §6's running order for Chapter 3 — *the loop leads, the optimizer serves it* |
| `D11_poc_report.md` | 227 | The PoC report for the advisor: four answers, the differentiator, limitations |
| `PoC_and_Validation_Plan.md` | 374 | September's scope, deliverables D1–D12 with owners and dates (§5.2), ownership (§5.5), risks |
| `M1_Proposal_Presentation_Slides.md` | 217 | Slide-by-slide with speaker scripts. **Check every figure against the corrections table first** |

### `docs/sessions/` — what we run with people

| File | Lines | What it is |
|---|---|---|
| **`T0_briefing.md`** | 156 | **How to run the 8 Sep session.** Confirm-or-object, a default for every item, the sign-off template |
| `T0_Formulation_Ratification_Briefing.md` | 134 | The **formal model** being ratified — the mathematics and the problem classification. Read this for *what*; read the above to *run the meeting* |
| `study_guide.md` | 238 | Preparing to be questioned. Things to **run and predict**, not to read. Step 9 rehearses the hard questions |

### `docs/presentation/`

| File | Lines | What it is |
|---|---|---|
| `T0_full_deck.html` | 1780 | Self-contained 30-slide deck, no dependencies — open in a browser. Covers problem → design → PoC → findings → the T0 decisions. `←`/`→` navigate, `N` speaker notes, `D` dark mode, `Ctrl+P` prints with notes |

### `docs/research_papers/` — literature tracking, feeds Chapter 2

| File | What it is |
|---|---|
| `papers.json` | The reference database. **The source of truth for every citation** |
| `relationship_report.md` | Generated prose report on how the papers relate to each other and to us |
| `relationship_map.mmd` | Mermaid diagram of the same |
| `HOW_TO_ADD_A_PAPER.md` | The process. Read before touching `papers.json` |
| `NEW_PAPER_TEMPLATE.json` | Skeleton entry |
| `build_report.py` | Regenerates `relationship_report.md` from `papers.json` |
| `generate_diagram.py` | Regenerates the Mermaid map |
| `integrity_check.py` | Validates `papers.json` structure |
| `check_no_shrinkage.py` | Guards against a paper silently losing content on edit |
| `growth_log.json` | Append-only record of how the database grew |
| `snapshots/*.json` | 14 before/after snapshots taken around each paper addition (P1, P6–P12). Evidence that no entry was lost or quietly rewritten |

### `docs/v1_superseded/` — the retired v1 design

Not current. Its `README.md` says what replaced what and why. Kept because v1's errors are
instructive — notably the **slot ledger** it modelled, which v2's `ProvisioningState` replaced.

| File | What it is |
|---|---|
| `README.md` | What was superseded, and why |
| `ARCHITECTURE.md` | The v1 design, 532 lines |
| `SCHEDULE.md` | The v1 schedule |
| `offline_baselines/` | v1's standalone MILP baselines — `milp_baseline.py`, `scenario2_order_sensitivity.py`, plus a README |

---

## `poc/` — the proof-of-concept

**This is the code that matters.** Built in a strict order where each step was verifiable
before the next, because nothing can be checked for correctness without ground truth.

`poc/README.md` (51 lines) is the package's own entry note.

### `poc/formulation/` — the problem, as data and as assertions

> *No algorithms live here.*

| File | Lines | What it is |
|---|---|---|
| `types.py` | 142 | **The data model.** `Task`, `ProfileSpec`, `AllocationResult`, `Infeasible`, `AdmitCost`, `Observation`. Also where **O1 is resolved as "no"** — there is no `varcost` field, so the objective is provisioning cost only |
| **`invariants.py`** | 86 | **I1–I5, asserted on every allocation result in every test.** The single highest-value piece of test infrastructure in the repo — all three tracks have relaxation or rounding steps that can silently emit invalid answers |
| `__init__.py` | 5 | |

### `poc/core/` — what every track shares

| File | Lines | What it is |
|---|---|---|
| **`provisioning.py`** | 141 | **`ProvisioningState` — the centre of the design.** Owns `n[m]`, load per profile, GPUs used. `cost_to_admit()` returns `extra_instances = 0` when headroom already covers the task — **that state-dependence *is* the aggregate-coupling problem.** Get this wrong and every number is wrong |
| `decision_rule.py` | 52 | `select_profile` — the one inner rule all three tracks call (**principle P4**). The `cost_adjust` argument is the only thing that differs between tracks |
| `consolidation.py` | 196 | The multi-move neighbourhood: relocate every task on one profile together. Also holds `consolidate_subsets` (k ≤ 2), which is what recovers the fixture's optimum |
| `relocate.py` | 63 | Single-move relocate — move one task, keep strict improvements. **Provably insufficient on the fixture**, which is why it exists as its own condition |

### `poc/instances/` — the problems we solve

| File | Lines | What it is |
|---|---|---|
| `generator.py` | 174 | The **uniform** generator. `price = gpus × U(80,120)`. Also holds the shared budget anchor `_reference_gpus` and the pool builder |
| `structured_generator.py` | 158 | The **structured** generator — deliberately opposite structure: sublinear throughput, GPU tiers, lognormal loads, clustered floors |
| `heterogeneous_generator.py` | 219 | The **heterogeneous** generator — a local, owned, mixed fleet where price per GPU varies by hardware class. **Built to close F31**, and it reversed T3's answer |
| `fixtures/adversarial_3t2p.py` | 94 | **The ground truth.** 3 tasks, 2 profiles, B = 4, optimum **280**, greedy **300**. Hand-verified by exhaustion. Every track is tested against it |

### `poc/tracks/` — the allocators

The exact solver was built **before any heuristic**, deliberately.

| File | Lines | Condition | What it is |
|---|---|---|---|
| `exact_milp.py` | 184 | `MILP` | Direct MILP encoding in PuLP with CBC. **Ground truth — returns 280 on the fixture.** Also *is* the Murakkab baseline, since §1 is their model |
| `static_baseline.py` | 98 | `STATIC` | The no-optimisation floor. Shows optimisation is worth doing at all |
| `track_a_greedy.py` | 98 | `A` | Plain greedy. **Returns 300 on the fixture — which is the point**, and is an asserted test |
| `track_a_m1.py` | 143 | `A+M1` | Greedy + feasibility lookahead (the M1 analogue) |
| `track_a_relocate.py` | 47 | `A+rel` | Greedy + one relocate pass |
| `track_a_subset.py` | 59 | `A+subset` | Greedy + subset consolidation. **Recovers 280** |
| `track_a_m1_subset.py` | 55 | `A+M1+subset` | Both refinements together |
| `track_b_lagr.py` | 347 | `B` | **Lagrangian relaxation of (C1)** with subgradient updates. The shipped arm — the bound is the whole point |
| `track_b_cold.py` | 35 | `B-cold` | Track B with **no warm start**, so any "B beats A" claim can be read off an independent comparison |
| `track_b_c3.py` | 184 | `B-C3` | Relaxation of the **budget** constraint (C3), via bisection on a scalar μ |
| `track_b_budget.py` | 165 | `B-C3-alt` | An independent implementation of the same arm, kept so the alternative is reproducible rather than asserted |
| `track_b_capacity.py` | 176 | `B-C2` | Relaxation of the **capacity** constraint (C2). T1's third arm — worst of the three everywhere |
| `track_c_lp.py` | 227 | `C` | **LP relaxation + rounding + repair.** The practical workhorse — bounded, predictable runtime |
| `track_c_consolidate.py` | 59 | `C+cons` | Track C + the consolidation pass |
| `track_c_multi.py` | 40 | `C2` | Track C given every realisation order |

### `poc/harness/` — measurement

| File | Lines | What it is |
|---|---|---|
| **`runner.py`** | 250 | Runs **all 15 conditions under matched inputs** — every condition gets the *identical instance object*, which is what makes comparison legitimate. Holds the condition registry and the `UNAVAILABLE` map that names what is *not* being run, out loud. `python -m poc.harness.runner` |
| `metrics.py` | 121 | Cost, runtime, bound, gap, feasibility. `gap_to_optimum`, `bound_gap`, `summarise`, `solvability` |

### `poc/tests/` — 647 passing, 4 skipped

| File | Lines | What it covers |
|---|---|---|
| `test_provisioning.py` | 183 | Admit sequences, headroom arithmetic, budget rejection, snapshot/restore |
| `test_invariants.py` | 105 | `invariants.check()` against hand-built valid *and violating* results |
| `test_adversarial.py` | 126 | The fixture — including that greedy really does return 300, and that all six orderings do |
| `test_tracks_small.py` | 239 | Every track against the exact optimum **by exhaustion**, on instances small enough to enumerate |
| `test_track_b.py` | 327 | The bound is the point, so the bound is the test. `bound ≤ optimum` is a disqualifying-if-broken property. Also covers bound survival on a failed primal |
| `test_harness.py` | 225 | Reproduces a known result end to end under matched inputs |
| `test_decision_rule.py` | 87 | Known pools, hand-computed answers, all-infeasible returns `None` |
| `test_consolidation.py` | 111 | The multi-move pass |
| `test_generator.py` | 94 | Well-formed instances, every `C(t)` non-empty, reproducible from seed |
| `test_structured_generator.py` | 111 | Same contract, *and* assertions that it is genuinely different |
| `test_heterogeneous_generator.py` | 152 | Same, plus **corr(price, gpus) asserted in both directions** — near zero here, near one there |

---

## `prototype/` — the closed loop

> **Outside the September PoC scope.** `prototype/README.md` says so before you use anything
> here. It exists because the loop is the project's contribution and had to be shown to work,
> not because the PoC needed it.

| File | Lines | Job | What it is |
|---|---|---|---|
| `loop.py` | 184 | — | **The closed loop**: J1 → J2 → J3 → J4 → J5 → J6 → J7 → J8 → J9 → J3 … |
| `ingestion.py` | 119 | J1 | Parse, validate, **freeze** a batch |
| `registry.py` | 95 | J2 | Executor Registry + Eligibility Resolver — builds `C(t)` |
| `simulator.py` | 121 | J5/J6 | A **simulated** executor that emits `Observation`s. *This is the biggest threat to every loop result* |
| `profiling.py` | 219 | J7/J8 | Profile Store with EMA updates, and the Drift Detector. Note §4.5's EMA was **wrong for reliability** and was replaced with a counting estimator (F19) |
| `reoptimisation.py` | 129 | J9 | Global and scoped re-optimisation. Scoped is **vacuous** — see O9/F18 |
| `tests/test_loop.py` | 227 | | The loop end to end |
| `tests/test_profiling.py` | 186 | | Store and detector |
| `tests/test_registry.py` | 69 | | §4.2's previously untested claim, now tested |
| `tests/test_reoptimisation.py` | 167 | | The **O9 experiment** — scoped vs global |

---

## `scripts/` — each one reproduces a finding

Every script here exists so a claim can be re-derived from scratch rather than trusted.

| File | Lines | Reproduces |
|---|---|---|
| `audit_budget_binding.py` | 134 | **T3 / F33.** Holds tasks and profiles fixed, varies *only* B, and asks whether the optimum moves. 0–4/25 vs **24/25** |
| `audit_t1_arms.py` | 155 | **T1 / F34–F35.** All three relaxation arms against the LP bound, paired, with bootstrap intervals |
| `audit_f20_subset.py` | 172 | **T2 / F32.** The paired audit that retired the "twenty-fold improvement" claim |
| `generate_chapter3_tables.py` | 157 | The Chapter 3 scale benchmark tables and their LaTeX |
| `prepare_multiworkflow_batch.py` | 134 | Turns real Zookeeper LogHub data into a concrete multi-workflow batch |

---

## `data/`

| File | Lines | What it is |
|---|---|---|
| `eval_batches/eval_batch_3workflows.json` | 3430 | The prepared multi-workflow evaluation batch |

*(Raw LogHub samples — `linux_sample.log`, `spark_sample.log`, `zookeeper_sample.log` — are
inputs to `prepare_multiworkflow_batch.py`.)*

---

## Reading paths

**"I have one hour and know nothing."**
`docs/ORIENTATION.md` → `docs/evidence/poc_findings_summary.md`. Done.

**"I need to understand the maths."**
`docs/design/System_Architecture_v2.md` §1 → `poc/formulation/types.py` →
`poc/instances/fixtures/adversarial_3t2p.py`. The fixture makes §1 concrete in 90 lines.

**"I need to understand why it is hard."**
The fixture, then `poc/core/provisioning.py` — specifically `cost_to_admit`. That one method
is the difficulty.

**"I am going to change an algorithm."**
`CLAUDE.md` first (the scope guard and the settled decisions), then
`docs/design/component_reference.md`, then the track. **Run `pytest` before and after** —
I1–I5 will catch most mistakes immediately.

**"I need to check whether a number is safe to quote."**
`docs/evidence/poc_findings_summary.md`, the *"numbers that were corrected"* table. Always.

**"I am presenting."**
`docs/presentation/T0_full_deck.html` → `docs/sessions/study_guide.md` step 9.

---

## Where to make a change

| If you want to… | Touch | And check |
|---|---|---|
| Change the objective or a constraint | `poc/tracks/exact_milp.py` **and every track** | This is expensive. See O1 in `CLAUDE.md` first |
| Add an allocator | a new `poc/tracks/*.py` + register it in `harness/runner.py` | It must return `AllocationResult` and pass I1–I5 |
| Add an instance family | a new `poc/instances/*_generator.py` | Mirror `test_heterogeneous_generator.py` — assert it is *different*, not just valid |
| Change how capacity is counted | `poc/core/provisioning.py` | Everything. This is the centre |
| Add a finding | append to `docs/evidence/poc_findings.md`, then update `poc_findings_summary.md` | The log is chronological — **append, never rewrite history** |
| Fix a retracted number | `poc_findings_summary.md` corrections table, then sweep every document | `PLAN.md` step 3 is exactly this task |

---

## Two conventions that are easy to violate by accident

1. **`docs/evidence/poc_findings.md` is append-only history.** Findings that were later
   corrected stay as they were written; the correction is a *new* finding that supersedes
   them. The summary states the current position. Rewriting the log destroys the audit trail
   that is this project's strongest asset.

2. **Never divide two means.** Report the paired per-instance difference and its interval.
   Four headline numbers were retracted for exactly this. If you are about to write `N×`,
   stop and compute the paired statistic instead.
