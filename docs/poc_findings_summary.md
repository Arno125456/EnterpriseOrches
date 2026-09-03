# PoC Findings — standing summary

**Read this instead of `poc_findings.md` unless you need the history.** As of 3 September
2026, that log runs to seventeen findings, several of which correct earlier ones — F14 was
corrected by F15 and again by F16; F6 was refined by F17; F7's headline number was amended
by F12. The history is deliberate and worth keeping, but it is archaeology. This page states
what we believe *now*.

Every row carries what would overturn it, because most of these have been overturned at
least once already.

---

## The four questions

### T1 — Does the Lagrangian relaxation decompose, and along what axis?

**Answered.** Both candidate decompositions are now built and measured:
- **Relaxing (C1)** decomposes **per profile** into 0/1 knapsack subproblems (`tracks/track_b_lagr.py`). Its bound is strictly tighter than the LP bound on 30 of 30 instances (0.12% vs 21.86% on the fixture), but its knapsack DP is computationally expensive.
- **Relaxing (C3)** decomposes **per task** with a single scalar multiplier μ (`tracks/track_b_c3.py`, condition `B-C3`). Its 1D concave dual problem solves in < 1 ms via bisection, and its optimal dual bound matches Track C's LP bound (as linear programming duality predicts).

**Conclusion:** Relaxing (C1) provides the superior dual bound; relaxing (C3) provides an ultra-fast alternative whose bound matches the LP bound.

### T2 — Does greedy construction survive aggregate coupling?

**No, but multi-move subset consolidation recovers it.** On the hand-verified fixture, plain greedy returns 300 against an optimum of 280, and neither multi-start nor single-move relocate recovers it.

**The resolution:** `core/consolidation.py` now implements `consolidate_subsets` (condition `A+subset` in `tracks/track_a_subset.py`). By evaluating joint k-subset moves, it moves {t1, t2} to m2 together while keeping t3 on m1, **recovering the exact global optimum of 280** (findings F20).


### T3 — Over what budget range does the problem have interesting structure?

**Answered, but the experimental design is defective.** Solvability rises from 1/25 to 25/25
as tightness goes 0.5 → 1.0, so a binding region exists and is wide.

**The defect:** the sweep only runs *below* the reference allocation, and F15 showed the
cliff sits exactly *at* it — every track goes from 0/5 to 5/5 feasible with 25% more budget.
Everything measured at `tightness = 1.0` was measured on a cliff edge. **T3's sweep must
extend above the reference before D9 is written.**

### T4 — Is Track A worth its complexity relative to Track C?

**No, and the honest answer is regime-dependent.**

| regime | verdict |
|---|---|
| ≤ 8 tasks | **No heuristic is justified at all.** The MILP is optimal in 32 ms |
| 16–128 tasks | **Track C, decisively.** Greedy sits 8–15% off and degrades with scale |

At 128 tasks on the instance family where the MILP is actually expensive, **Track C is ~110×
faster for under 5% cost** (17.75 s → 0.162 s, 4.58% gap). That is the result Objective
1.2.2 asks for, and it is the only clean instance of it in this work.

---

## What we believe, and what would overturn it

| # | Belief | Confidence | Evidence | Overturned by |
|---|---|---|---|---|
| 1 | Greedy is defeated by aggregate coupling; multi-start and single-move relocate cannot recover | **High** | Hand-verified fixture, re-derived by exhaustive enumeration in tests | Nothing short of an arithmetic error in the fixture |
| 2 | Track C at scale is ~110× faster than exact for <5% cost | **Medium-high** | F16, 3 seeds, uniform generator, 1.25× budget | More seeds; a generator where the MILP stays cheap |
| 3 | The Lagrangian bound is consistently tighter than the LP bound | **High** | 30/30 strictly tighter, 0 invalid; rounding errs *against* Track B | An instance class where they converge |
| 4 | Track B is not viable as an allocator — ~100× slower than the exact method it replaces | **Medium** | F13, timings at 8/16/24/32 tasks | **A profiled implementation.** The knapsack DP is pure Python and could plausibly gain an order of magnitude |
| 5 | The LP prices profiles by *rate*, so it cannot see that a large profile's integer instance will sit mostly empty | **High** | F17, fully diagnosed on a specific instance; the fix halves Track C's gap on both generators | Nothing — the mechanism is arithmetic |
| 6 | The shared decision rule ignores `extra_gpus`, which causes infeasibility | **High** (mechanism) / **Low** (rate) | §5.2.1 by inspection; but the 42% rate is an anchor artefact | The mechanism is in the spec. The *rate* should never be quoted |
| 7 | A feasibility lookahead (A+M1) substantially cuts greedy's failures at no runtime cost | **Medium-high** | 27→17 uniform, 29→2 structured | Scale — untested past 32 tasks |
| 8 | Optimisation beats no-optimisation by a wide margin | **High** | STATIC 23–25% off, fails 58% of instances | Nothing plausible |
| 9 | The exact MILP becomes expensive around 128 tasks — but only on some instance families | **Medium** | 21 s uniform vs 1.9 s structured at 128 | More families; a better solver or formulation |
| 10 | Instance *structure* drives solver cost more than instance *size* | **Medium** | Structured was harder at 8 tasks, 11× cheaper at 128 | Only two generators exist |
| 11 | Scoped re-optimisation is well-defined but **vacuous**: a drifted profile is used by 84-100% of workflows, so the affected set is almost the whole batch. Scoped narrower than reality it costs a mean 22%. Either way, do not build it | **Medium-high** | F18, corrected; 60 instances, workflow counts 2-12 | Global re-optimisation becoming expensive at scale |
| 12 | Section 4.5's EMA is wrong for reliability: a binary signal under an EMA reports 0.70 after 99 successes and one failure, and that value filters C(t) | **High** | F19, arithmetic, reproduced in tests | Nothing - the mechanism is arithmetic |

---

## Numbers that were corrected — do not quote the originals

| Stale claim | Where it came from | Current status |
|---|---|---|
| "Lagrangian bound is **6×** tighter" | F7, uniform generator only | **3–6×**, generator-dependent (F12) |
| "Both heuristics fail on **42%** of instances" | F3 | Mechanism real; the *rate* is an artefact of the budget anchor |
| "The greedy tracks **collapse at scale**" | F14 | **Wrong.** A cliff at exactly the anchor budget; 25% more budget restores 5/5 (F15) |
| "Track C's gap **improves monotonically** with size" | F14 | Also a cliff artefact. It sits in a 2–5% band with no clean trend (F16) |
| "Track C is the **weakest** of the three tracks" | F11, and an amendment I made to §5.9 | **Withdrawn.** True at 8 tasks, false at scale, where it is the only heuristic that works |
| "**Track B dominates**" | F10 | True on quality at 8 tasks; false in practice — it is ~100× slower than exact (F13) |
| "Rounding the routing is **nearly free**" | F6 | Mechanically true, but the integral routing can still be badly wrong (F17) |
| "Scoped re-optimisation is **worse ~50% of the time**" | F18, first version | Measured an arbitrary affected workflow rather than the drifted profile's. Correctly scoped it is **identical to global**, because the affected set is 84-100% of workflows |

---

## What none of this establishes

- **Nothing about real workloads.** Two synthetic generators, both written by the same author
  as the tracks and the metrics. Real data is out of PoC scope by §5.1.
- **Nothing statistical.** Scale runs are 3 seeds; tightness sweeps are 25. No confidence
  intervals, no significance testing.
- **Nothing about Track B's real ceiling.** Its runtime finding may be implementation, not
  method.
- **Nothing about execution or the domain.** No allocation has been run against a real
  executor, and R7/R8/R9 have no implementation.
- **Profiling and drift exist only as a prototype.** `prototype/` implements the Profile
  Store, Drift Detector and J9 outside PoC scope, fed synthetic observations. The
  compatibility score there is **[PROPOSED]** and not the source paper's, so no number from
  it should be quoted until 077 reconciles it.
- **No claim of the form "our approach reduces cost by X%"** is supported.

---

## Outstanding, in priority order

| # | Item | Owner | Status / Due |
|---|---|---|---|
| 1 | **T0 / D1 — ratify the formulation.** Everything above rests on §1 being right | All | **8 Sep** |
| 2 | Extend T3's sweep *above* the reference (`runner.py`) | 089 | **Done** (F22) |
| 3 | Ask the advisor what "improve reliability" means — floor, or objective? One reading changes §1 | Advisor | before T0 |
| 4 | Build the (C3) relaxation arm so T1 is actually answered (`track_b_c3.py`) | 075 | **Done** (F21) |
| 5 | Profile Track B's knapsack subproblem before its runtime finding is treated as settled | 075 | — |
| 6 | Subset-move neighbourhood — closing both T2's fixture and F17 (`track_a_subset.py`) | 035 | **Done** (F20) |
| 7 | Reconcile `track_a_m1.py` against Cheng & Nguyen's actual M1 | 035 | — |
| 8 | More seeds before anything reaches Chapter 3 | 089 | before D11 |
| 9 | **Drop scoped re-optimisation from Semester 2.** F18 answers O9: it works but is not worth building | 077 | - |
| 10 | Reconcile the [PROPOSED] compatibility score against Hatherley (2025) | 077 | - |
| 11 | **Amend section 4.5**: EMA for latency, decayed counting estimator for reliability (F19) | 077 | - |

---

## How to reproduce anything here

```bash
pytest poc/tests                 # 528 tests
python -m poc.harness.runner     # the tightness sweep
```

```python
from poc.harness.runner import sweep, scale_sweep      # scale_sweep for the size axis
from poc.harness import metrics
from poc.instances import structured_generator          # pass generator=... to either
```

Always read `infeas` beside `mean gap%`. A condition that only solves the easy instances
posts the best-looking gap in the table — `metrics.summarise` counts failures rather than
averaging over them precisely to make that visible, and the first scale scripts got this
wrong by bypassing it.
