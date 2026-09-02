# prototype/ — outside the September PoC scope

**Nothing here is a September deliverable, and none of it is required by T1–T4.**

`poc/` is scope-guarded by v2 §6.5 and `CLAUDE.md`: registry, profiling, execution and
re-optimisation are explicitly excluded because none of them helps answer T1–T4. That
guard is correct and this directory does not weaken it. `poc/` imports nothing from here.

## Why this exists anyway

Two claims in the architecture are load-bearing, untested, and cheap to test:

**1. §4.2 — "exact match only, so registry gaps surface as failures rather than silent
quality loss."** In the PoC, `C(t)` arrives pre-built from the instance generator, so no
code ever builds pools from a registry and this claim has never been exercised.

**2. §3.3 [OPEN — O9] — "scoped re-optimisation may not be well-defined."** The architecture
says J9 re-invokes J3 "for affected workflows only", then immediately doubts it: under (C2),
re-routing one workflow changes load on shared profiles, which changes instance counts,
which affects every other workflow using them. It is deferred to Semester 2.

The second one is worth testing in September precisely because it is deferred. If scoped
re-optimisation is not well-defined, that invalidates a component 077 would otherwise spend
a semester building, and §5.0's whole argument is that discovering such things late is the
expensive outcome.

## What is here

| Module | Covers | Status |
|---|---|---|
| `registry.py` | Executor Registry (§4.3) + Eligibility Resolver (§4.2) | Built |
| `profiling.py` | Profile Store with EMA + Drift Detector (§4.5) | Built, compatibility score is **[PROPOSED]** |
| `reoptimisation.py` | J9, global vs scoped (§3.3) | Built, to answer O9 |

Not here, and not attempted: the Execution Engine. Nothing can be executed without real
executors, and a mock one would test the mock.

## What is invented rather than sourced

The **compatibility score** in `profiling.py` is attributed in §9 to Hatherley (2025), which
is not available in this repo. The definition used here is invented and marked
**[PROPOSED]**: the fraction of tasks whose chosen profile is unchanged when the decision is
recomputed against updated profiles. It is defensible and matches §4.5's description
("recomputes the would-be decision under the updated profile"), but it is not the paper's.
**077 must reconcile it before any finding depends on the number.**
