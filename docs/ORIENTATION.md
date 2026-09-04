# Orientation — the whole project, from zero

**If you know nothing about this repo, read this file and nothing else.** It explains what the
project is, how the system is designed, what has actually been built and measured, and where
to look when you want more depth. Every claim here links to the document or file that backs
it.

Written 4 September 2026. Milestone **M1 is 30 September 2026**.

---

## 1. In five sentences

We are building a system that decides, for a batch of AI workflows, **which model serves each
task** and **how many copies of each model to pay for**, minimising cost under a fixed GPU
budget. Those decisions depend on *profiles* — how fast, how reliable, how expensive each
model is — and the usual approach treats profiles as fixed numbers typed in by a human. Ours
**measures profiles from real execution, notices when they drift, and re-allocates.** The
allocation maths itself is textbook and we say so; the loop around it is the contribution.
This repo currently holds a **proof-of-concept** built to test four specific questions before
the real system is written — it is not a small version of the system.

---

## 2. The problem, in plain language

You have a batch of workflows. Each workflow is a DAG of tasks — "summarise this", "extract
entities", "generate code". Each task could be served by several different **model profiles**:
a profile is a concrete deployable thing, roughly `(model, hardware tier, batch config)`, and
different profiles differ in throughput, price, reliability and latency.

Two decisions have to be made together, for the whole batch, before anything runs:

| decision | symbol | meaning |
|---|---|---|
| **Routing** | `x[t][m]` | which profile `m` serves task `t` — exactly one each |
| **Provisioning** | `n[m]` | how many instances of profile `m` we pay for |

You want the cheapest total bill, and you cannot exceed a GPU budget.

**Why this is not trivial.** The two decisions are coupled in a circle. Routing determines how
much load lands on each profile. Load determines how many instances you must buy. Instances
consume GPUs. A tight GPU budget constrains what routing you were allowed to choose in the
first place.

**Where the real difficulty lives** is subtler and it has a name in this project: *aggregate
coupling*. Capacity is bought in **whole instances**, not per task. So the cost of putting a
task somewhere depends on whether that profile already has spare room — which depends on
decisions you have not made yet. Two tasks that are each individually expensive to move can be
cheap to move *together*. Section 6 works through the smallest example we have.

---

## 3. What is ours, and what is borrowed

This is the honest positioning, and it is settled team policy — do not quietly upgrade it.

**Borrowed.** The allocation problem is a known one: **modular capacitated facility location
with a budget constraint.** Profiles are facilities, `n[m]` is units opened at a facility,
tasks are customers, the capacity constraint is facility capacity. We do not claim novelty
here and we present it as adopted. See `System_Architecture_v2.md` §1.8.

**Ours.** The **closed loop**: measure profiles from execution, detect drift, re-optimise.
Neither of the two closest papers does this — both take profiles as static inputs. The advisor
confirmed on 3 September that this is a sufficient novelty claim for M1 (open question O12).

**The evidence for it**, and the single most important number in the project: under drift, a
static allocator delivers **0.542 reliability against a 0.95 floor while reporting no change**,
where the adaptive loop holds **0.938**. Paired difference **+0.424 [0.405, 0.442]** over 20
seeds. That is finding F24.

The optimiser exists *because the loop needs one that is fast enough to re-run*. It is the
engine, not the contribution. `proposal_narrative.md` is the argument chain in full.

---

## 4. How the system is designed

### 4.1 The loop

The system is a cycle of jobs, J1 through J9. The prototype in `prototype/` implements it
end to end against a simulated executor.

```
   J1 ingest a batch of workflow DAGs          prototype/ingestion.py
        |
   J2 resolve eligibility  C(t)                prototype/registry.py
        |
   J3 ALLOCATE  (routing x, provisioning n)    poc/tracks/*.py
        |
   J4 provision instances                      poc/core/provisioning.py
        |
   J5/J6 execute, emit observations            prototype/simulator.py
        |
   J7 update profiles from what happened       prototype/profiling.py
        |
   J8 detect drift
        |
   J9 re-optimise  ------> back to J3          prototype/reoptimisation.py
```

**J3 is the part this repo has studied hardest**, because it is the part that has to be cheap
enough to run every time J9 fires.

### 4.2 Components

| component | what it does | state |
|---|---|---|
| **Multi-Workflow Optimizer** | J3 — solves the allocation | **built**, five families of algorithm |
| **Provisioning State** | owns `n[m]`, the budget, admit/release | **built**, `poc/core/provisioning.py` |
| **Eligibility Resolver** | builds `C(t)` from floors | **built** (prototype) |
| **Profiling Subsystem** | updates profiles, detects drift | **built** (prototype) |
| **Executor Registry** | catalogue of profiles | **stubbed** — generators supply profiles |
| **Execution Engine** | actually runs the work | **simulated only** — Semester 2 |

**`ProvisioningState` is the centre of the design.** Every track goes through it, and it is
where aggregate coupling is made concrete: `cost_to_admit()` returns `extra_instances = 0`
when existing headroom already covers a task. Get that wrong and every result is wrong.

### 4.3 One design correction worth knowing

An earlier version of the design had a "slot ledger" decremented per task assignment. **That
was wrong and is settled.** Capacity is consumed by *instances*, not by assignments — tasks
add *load*, and load may or may not force a new instance. Two other settled points: HEFT and
upward-rank scheduling are **not** used (there is no makespan term in the objective), and task
precedence affects execution order only, never the optimisation. See `CLAUDE.md`, "Things that
are settled".

---

## 5. The formal model

```
Variables
  x[t][m] ∈ {0,1}    task t routed to profile m ∈ C(t)
  n[m]    ∈ Z⁺       instances of profile m provisioned

Objective
  minimize  Σ_m n[m] · price(m)              ← provisioning cost only

Constraints
  (C1)  Σ_{m ∈ C(t)} x[t][m] = 1             ∀t   every task goes exactly one place
  (C2)  Σ_t x[t][m]·load(t) ≤ n[m]·thr(m)    ∀m   you must buy the capacity you use
  (C3)  Σ_m n[m]·gpu(m) ≤ B                        the GPU budget

Eligibility — applied when BUILDING C(t), not as a constraint
  C(t) = { m : rel(m) ≥ R_min(t)  and  lat(t,m) ≤ L_max(t) }
```

Three things people get wrong when they first read this:

1. **Reliability and latency are not constraints.** They are filters applied earlier, when the
   candidate list `C(t)` is built. A profile that fails a task's floor is never considered.
   Feasibility first, cost second. The advisor confirmed reliability is a **floor, not an
   objective** (O10, 3 September).
2. **There is no per-call cost.** The objective is provisioning cost only. This was open
   question O1 and it is closed — reopening it changes the objective everywhere.
3. **(C2) is the constraint that couples tasks to each other.** (C1) is per-task and (C3) is a
   single global line. (C2) is why this problem is hard, and it is the answer to "which
   constraint couples workflows?" — a question every team member is expected to answer
   unprompted.

---

## 6. Why it is hard — the example that teaches it

This fixture is three tasks and two profiles, small enough to solve by hand, and it is checked
by tests. `poc/instances/fixtures/adversarial_3t2p.py`.

```
Profiles                                   Tasks
  m1: thr=10 gpu=1 price=100 rel=0.99        t1: load=8  needs rel≥0.90  → {m1, m2}
  m2: thr=25 gpu=2 price=180 rel=0.95        t2: load=6  needs rel≥0.90  → {m1, m2}
                                             t3: load=9  needs rel≥0.98  → {m1} only
Budget B = 4
```

By exhaustion, the optimum is **280**: send `t1` and `t2` to `m2`, `t3` to `m1`.

Greedy construction gets **300**:

```
t1: m1 costs 100 (open one), m2 costs 180  → picks m1
t2: m1 has headroom 2 < 6, so +1 instance = 100; m2 = 180  → picks m1
t3: m1 has headroom 6 < 9, so +1 instance = 100; m2 ineligible  → m1
```

Each individual choice is correct and the total is wrong. `t1` and `t2` are each cheaper alone
on `m1`, but **together** they fit in one `m2` instance with room to spare.

And it is robust — verified exhaustively:

- **All six orderings** of the tasks give 300. Multi-start does not help.
- **Moving one task at a time** never helps: relocating `t1` alone costs +180 to save 100.
  Same for `t2`. The improving move is *both together*.

That is why the fix had to be a **subset move** (`A+subset`), which finds `{t1,t2} → m2` and
recovers 280. This one fixture drove a real algorithmic decision, which is what fixtures are
for.

---

## 7. The algorithms

Five families, plus baselines. All are registered as **15 runnable conditions** in
`poc/harness/runner.py` and every result is checked against invariants I1–I5 before it leaves
a track.

| | idea | what it is for |
|---|---|---|
| **MILP** | exact solve via CBC | ground truth. Also *is* the Murakkab baseline — the formulation is their model |
| **STATIC** | no optimisation | the floor. Shows optimisation is worth doing at all |
| **Track A** | greedy construction | fast, myopic. `A+subset` adds the subset move; `A+M1` adds a feasibility lookahead |
| **Track B** | Lagrangian relaxation | produces a **lower bound**, not really an allocator. Three arms relax (C1), (C2), (C3) |
| **Track C** | LP relaxation + repair | the practical workhorse — bounded, predictable runtime |

**Invariants, asserted on every result everywhere.** These are the single highest-value piece
of test infrastructure in the repo, because all three tracks have relaxation or rounding steps
that can silently emit invalid answers:

```
I1  every task appears exactly once            I4  every routed profile is in C(t)
I2  load routed to m ≤ n[m]·thr(m)             I5  n[m] ≥ 1 for every profile used
I3  Σ n[m]·gpu(m) ≤ B
```

---

## 8. The four questions, and where they stand

The PoC exists to answer these. **A negative answer is a success** — "Track B gives no
advantage" would save a semester.

| | question | current answer |
|---|---|---|
| **T1** | Which constraint should Track B relax, does its bound beat the LP? | **(C1).** Tighter than the LP on **53/53** instances across all three generators *wherever Track B has a feasible incumbent*. The (C2) arm is worst everywhere. (C3) collapses to the LP bound by theory |
| **T2** | Can greedy be defeated by aggregate coupling? | **Yes** — proven on the fixture and confirmed at scale. `A+subset` fixes it: **never worse** than plain greedy on 72 paired instances |
| **T3** | Over what budget range is there interesting structure? | **Wherever price per GPU is not constant.** The budget changes the optimal cost in **24/25** heterogeneous instances against **0–4/25** where price tracks GPU count |
| **T4** | Is Track A worth its complexity vs Track C? | **Plain greedy, no. `A+subset`, yes** — it is competitive. Track C's real virtue is *bounded* runtime, not average speed |

Two of those answers only exist because of work done in the last two days, and both came from
noticing that a measurement was shaped by an assumption:

- **T3** was "the budget is nearly inert" for weeks. It was inert *in our instances*, because
  both generators set `price = gpus × constant` — a homogeneous fleet, which contradicts this
  project's own premise of heterogeneous profiles. A third generator with price decorrelated
  from GPU count reversed the result completely (F31 → F33).
- **T1** briefly looked like it had collapsed on the new generator. It had not: that was a
  confound — instances where Track B finds a primal were pooled with instances where it does
  not. Split, the advantage is intact (F34 → F35).

---

## 9. How this project treats evidence

This matters more than any single result, and it is the thing to imitate if you join.

**Three headline numbers were retracted by our own audit**, and a fourth was found later. All
failed the same way: **a ratio of two means**, which is not a typical ratio when either
distribution has a tail. "Track C is ~110× faster" was `12.283 / 0.106`; the *median* speedup
is 5×.

The rules that came out of it:

1. **Never divide two means.** Report the paired per-instance difference and its interval.
2. **A paired interval that crosses zero means the effect is not established.**
3. **Check `poc_findings_summary.md`'s "numbers that were corrected" table before quoting any
   number.** Treat a bare `N×` claim with no interval as unverified.
4. **The audit is not a one-time pass.** Anything merged from a branch is unaudited whatever
   its finding number — F20 arrived after the audit ran and carried the same defect for a week.
5. **Before reporting a pooled difference, ask what would make an instance behave differently,
   and split on it.** This caught two errors, one inherited and one our own.

**Volunteer the limitations before you are asked.** An examiner who has to extract a weakness
trusts you less than one you hand it to. This project has unusually good material for that.

---

## 10. What actually exists right now

```
647 tests pass, 4 skip          35 findings recorded, including superseded ones
15 runnable conditions           3 instance generators
```

**Built and measured:** the formulation, an exact MILP validated against a hand-computed
optimum, three families of heuristic with valid bounds, the provisioning state, the invariant
checker, three generators, an evaluation harness, and a closed loop running against a
simulated executor.

**Deliberately not built** — see the scope guard in `CLAUDE.md`:
the executor registry, real profiling, real execution, drift-triggered re-optimisation in
production, framework integration, monitoring.

**The main open items**, if you are looking for something to work on:

| | what | who |
|---|---|---|
| **O5** | Track B's step-size schedule. Promoted from "untuned defaults" to blocking — where Track B has no incumbent its bound stalls below the LP's, which the dual optimum cannot do | 075 |
| — | **Track B's feasibility** — 7 of 17 on heterogeneous instances. The bound is fine; finding a primal is not. This is the interesting problem now | 075 / 089 |
| **O11** | Framework integration or standalone | Advisor |
| — | The compatibility score is `[PROPOSED]` and the paper it should reconcile with is not in the repo | 077 |
| — | Profile Track B's knapsack subproblem before its runtime finding is treated as settled | 075 |

---

## 11. Where to look next

**Read in this order if you want the full picture:**

| # | document | what you get |
|---|---|---|
| 1 | this file | the whole thing at low resolution |
| 2 | [`poc_findings_summary.md`](poc_findings_summary.md) | what we believe now, at what confidence, plus the corrections table |
| 3 | [`proposal_narrative.md`](proposal_narrative.md) | why the findings form one argument |
| 4 | [`System_Architecture_v2.md`](System_Architecture_v2.md) | the design of record. §1 is the formulation, §1.8 the problem class |
| 5 | [`poc_findings.md`](poc_findings.md) | all 35 findings in order, including retracted ones |

**Read by what you are doing:**

| you are… | read |
|---|---|
| going to the 8 Sep ratification | [`T0_briefing.md`](T0_briefing.md) — confirm-or-object, a default for every item |
| about to be questioned on this | [`study_guide.md`](study_guide.md) — things to run and predict, not to read |
| writing Chapter 3 | [`D11_poc_report.md`](D11_poc_report.md) then `proposal_narrative.md` §6 |
| changing code | [`../CLAUDE.md`](../CLAUDE.md) for the guardrails, [`component_reference.md`](component_reference.md) for behaviour |
| looking at a diagram | [`pipeline.md`](pipeline.md) |
| planning | [`../PLAN.md`](../PLAN.md) — eight steps to M1 |

**The code, in the order it was built** (each step was verifiable before the next):

```
poc/formulation/types.py        the data model
poc/formulation/invariants.py   I1-I5, called everywhere
poc/instances/                  generators + the hand-verified fixture
poc/tracks/exact_milp.py        ground truth — returns 280 on the fixture
poc/core/provisioning.py        THE central component
poc/core/decision_rule.py       shared routing rule
poc/tracks/track_c_lp.py        LP relaxation + repair
poc/tracks/track_b_lagr.py      Lagrangian bound
poc/tracks/track_a_greedy.py    greedy — returns 300 on the fixture, which is the point
poc/harness/                    matched-condition runner + metrics
prototype/                      the closed loop, against a simulated executor
scripts/audit_*.py              the statistical audits, each reproducing one finding
```

**Run it:**

```bash
python -m poc.harness.runner        # all 15 conditions
python -m pytest -q                 # 647 pass, 4 skip
python scripts/audit_budget_binding.py   # the T3 result, from scratch
```

---

## 12. Glossary

| term | meaning |
|---|---|
| **profile** | a deployable `(model, hardware, batch config)` with measured throughput, price, reliability, latency |
| **routing** / `x` | which profile serves each task |
| **provisioning** / `n` | how many instances of each profile are paid for |
| **`C(t)`** | a task's candidate list — profiles passing its reliability and latency floors |
| **aggregate coupling** | capacity is bought in whole instances, so a task's marginal cost depends on decisions not yet made. The core difficulty |
| **bound / bound gap** | a lower bound on the true optimum, and how far below it sits. Tracks B and C produce them |
| **condition** | one runnable allocator configuration in the harness. There are 15 |
| **paired difference** | same instance, two methods, difference per instance. The correct statistic here |
| **T0 / D1** | the 8 September session where the team ratifies the formulation |
| **M1** | the 30 September milestone — proposal and presentation |
