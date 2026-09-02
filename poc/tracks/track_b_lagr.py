"""
Track B — Lagrangian relaxation with subgradient updates.

Spec: docs/System_Architecture_v2.md §5.2.3.
Build step 8. Verified by: bound ≤ MILP optimum; bound vs LP bound — that is T1.
Owner: 075

WHICH CONSTRAINT TO RELAX IS [OPEN — T1/O2]. Do not settle it silently.

    relax (C1) assignment   → (C2) per profile, (C3) global  → per-profile subproblems
                              classical for capacitated facility location; §1.8 predicts this
    relax (C3) budget       → (C1) still couples profiles through tasks → no clean decomposition

v1 claimed per-workflow decomposition. §1.8 says that is wrong: (C2) is indexed by profile,
not by workflow. T1 confirms or corrects before this is built out.

The row to watch in T1: if the Lagrangian bound equals the LP bound consistently, Track B
provides nothing Track C does not, and the track should be cut or rejustified. Far better to
know on 15 September than in February (PoC plan §5.3 T1).

solve_profile_subproblem decides n[m] and which eligible tasks to take, given multipliers.
Because n[m] is a ceiling of load over throughput, the subproblem is itself a small integer
problem — this is where the bound can beat the LP.

[OPEN — O5] step-size schedule, convergence tolerance, iteration cap, primal repair heuristic.
On hitting the iteration cap: return best feasible found, flagged unconverged, with bound.
"""


def allocate(tasks, pools, profiles, budget, seed=0):
    raise NotImplementedError("Build step 8 — see docs/System_Architecture_v2.md §5.2.3")
