# Profile-Guided Multi-Workflow Resource Orchestration Platform

Senior capstone project — team of 5, advised by Prof. Tossaphol.

> ### New here? Read [`docs/ORIENTATION.md`](docs/ORIENTATION.md).
> One file, from zero: the problem, the design, what is built, what we found, and where to
> look for more. It assumes nothing. Everything below assumes you have read it or already
> know the project.

**Then:** [`CLAUDE.md`](CLAUDE.md) is the working summary and the guardrails.
[`docs/System_Architecture_v2.md`](docs/System_Architecture_v2.md) is the full design
reference; [`docs/PoC_and_Validation_Plan.md`](docs/PoC_and_Validation_Plan.md) is what
September is for; [`docs/pipeline.md`](docs/pipeline.md) is the end-to-end ASCII diagram
of the PoC pipeline. If code and a document disagree, the document is not automatically
right — flag the mismatch and resolve it explicitly, don't silently follow either one.

## What this project is

Multi-workflow resource orchestration in which the profiles that drive allocation are
**measured and kept current**, and the system **re-allocates when they drift**. The optimizer
is the engine that makes that loop affordable, not the contribution itself — see
[`docs/proposal_narrative.md`](docs/proposal_narrative.md) for the argument and the evidence
chain behind it.

The allocation problem underneath: a batch of workflows, each a DAG, and — for the whole
batch at once, offline — decide **which model profile serves each task** and **how many
instances of each profile to provision**, minimising provisioning cost under a fixed GPU
budget.

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

> **Start here: [`PLAN.md`](PLAN.md)** — eight steps in order, from today to the M1
> presentation. No options, no parallel tracks.
>
> Behind it: [`HANDOFF.md`](HANDOFF.md) for state and decisions already taken,
> [`BRANCHES.md`](BRANCHES.md) before merging anything.

## Where to start, by role

Nine documents exist. Nobody needs to read them all. Read the two marked **everyone**, then
the row for your part.

| | read | why |
|---|---|---|
| **everyone** | [`docs/T0_briefing.md`](docs/T0_briefing.md) | The 8 Sep session. Short, and it is the only thing with a deadline |
| **everyone** | [`docs/poc_findings_summary.md`](docs/poc_findings_summary.md) | What we currently believe, at what confidence. Includes a table of numbers **not** to quote |
| **presenting** | [`docs/study_guide.md`](docs/study_guide.md) | Nine steps to being able to defend every choice. Things to run and predict, not to read |
| 035 — Track A | `poc/tracks/track_a_greedy.py`, `track_a_m1.py`, findings F1, F8, F20 | Your track, and the M1 analogue that needs your sign-off |
| 075 — Tracks B & C | `poc/tracks/track_b_lagr.py`, `track_c_lp.py`, findings F7, F13, F16, F17, **F29–F30** | The bound result, and the **bounded-latency** result that carries Objective 1.2.2 — 0.106 ± 0.020 s against 12.3 ± 10.3 s. The 110× speedup it replaces is retracted; F29–F30 audited both |
| 077 — Phase C | `prototype/profiling.py`, `loop.py`, findings F18, F19, F23 | The profiling loop, and the two design decisions awaiting your sign-off |
| 083 — Infrastructure | `poc/instances/`, findings F2, F11, F12 | The generators and the budget anchor you need to accept or reject |
| 089 — Evaluation | `poc/harness/`, findings F10, F14, F15, F16 | The harness, and four cases where the experimental design misled us |

Then, when you need them:
[`docs/proposal_narrative.md`](docs/proposal_narrative.md) for what the findings are *for*,
[`docs/component_reference.md`](docs/component_reference.md) for what each part does and must
become, and [`docs/poc_findings.md`](docs/poc_findings.md) for the full chronological record
including superseded findings.


## Repo layout

```
CLAUDE.md                 Working summary + guardrails. Read first
docs/
  System_Architecture_v2.md   Authoritative design reference
  PoC_and_Validation_Plan.md  Scope, deliverables, schedule, risks
  D11_poc_report.md           The PoC report for the advisor — the four answers, the
                              differentiator, and what we do not know
  T0_briefing.md              READ FIRST if D1 has not happened — the 8 Sep session
  proposal_narrative.md       What the contribution is, and why the optimizer serves it
  component_reference.md      Per-component: behaviour, whether it earns its place, and
                              what it must become in the full system
  poc_findings_summary.md     START HERE for results — current beliefs and confidence
  poc_findings.md             Full chronological log, including superseded findings
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

Nine of the ten build steps are done and tested. Only step 8, Track B, is unbuilt: which
constraint it relaxes is T1's question (O2), and picking one would prejudge the test the
track exists to feed.

Results: [`docs/proposal_narrative.md`](docs/proposal_narrative.md) explains what the
findings are *for*, and [`docs/component_reference.md`](docs/component_reference.md) says
what each part does and what it needs to become. [`docs/poc_findings_summary.md`](docs/poc_findings_summary.md) is the
standing summary — what is believed now, at what confidence, and what would overturn it.
[`docs/poc_findings.md`](docs/poc_findings.md) is the full chronological log behind it.

## Build order

Do not reorder — each step is verifiable before the next, and **the exact solver comes before
any heuristic** because nothing else can be checked for correctness without ground truth.

| # | Build | Verify by | Status |
|---|---|---|---|
| 1 | `formulation/types.py` | Types instantiate | Done |
| 2 | `formulation/invariants.py` | Hand-built valid and violating results | Done |
| 3 | `instances/generator.py` | Instances well-formed; every `C(t)` non-empty | Done |
| 4 | `tracks/exact_milp.py` | **Returns 280 on `adversarial_3t2p`** | Done — also matches independent brute force on 36 random instances |
| 5 | `core/provisioning.py` | admit/release/snapshot/restore; budget rejection | |
| 6 | `core/decision_rule.py` | Known pools, known picks; all-infeasible returns None | |
| 7 | `tracks/track_c_lp.py` | Bound ≤ MILP optimum; satisfies I1-I5 | |
| 8 | `tracks/track_b_lagr.py` | Bound ≤ optimum; compare to LP bound (T1) | **Blocked — O2/T1 is 075's call** |
| 9 | `tracks/track_a_greedy.py` | Satisfies I1-I5; **returns 300 on `adversarial_3t2p`** | |
| 10 | `harness/` | Reproduces a known result end-to-end | Done — `python -m poc.harness.runner` |

## Getting started

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "import pulp; print(pulp.listSolvers(onlyAvailable=True))"   # expect PULP_CBC_CMD
pytest poc/tests
python -m poc.harness.runner   # regenerates the sweep in docs/poc_findings.md
```

Verified from a clean clone on 3 September 2026: fresh virtualenv, install from
`requirements.txt`, **565 passed in 79s**, and `poc.harness.runner` reproduced every figure
in the findings byte-for-byte. If any of that fails for you it is an environment problem,
not a repo problem — say so rather than working around it.

## Scope guard

> If a module does not help answer T1, T2, T3 or T4, it does not belong in the PoC.

Not built, deliberately: Executor Registry, Profiling Subsystem, Execution Engine, drift
detection and re-optimisation, Zookeeper/LogHub domain data, monitoring, fallback, framework
integration, and Track A's relocate/consolidate/elaborate multi-start. Full list in
`CLAUDE.md`.

## O1, and how it was settled

The objective is **provisioning cost only** — no per-invocation `Σ x[t][m]·varcost(t,m)`
term. That is `CLAUDE.md`'s stated default, adopted so build step 1 could proceed; it is a
default, not a team decision. It is recorded in `poc/formulation/types.py` where it bites.
If the team adopts usage-based pricing, the objective signature changes everywhere.

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
