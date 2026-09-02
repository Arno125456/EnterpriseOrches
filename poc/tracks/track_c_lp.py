"""
Track C — LP relaxation + rounding.

Spec: docs/System_Architecture_v2.md §5.2.4.
Build step 7. Verified by: bound ≤ MILP optimum; result satisfies I1-I5.
Owner: 075

Solve with x[t][m] ∈ [0,1] and n[m] ≥ 0 continuous, then round and repair.

Rounding is not incidental here. The LP returns fractional n[m]. Rounding down breaks (C2);
rounding up may break (C3); and rounding one profile up changes headroom that affects
whether another profile's rounding is feasible. Treat it as an algorithm, not a policy
switch. Repair failure returns Infeasible — never a violating assignment.

[OPEN — O6] the rounding policy itself, resolved by T3/T4.

Of the three tracks this one is stable — least affected by PoC outcomes
(PoC plan §5.9).
"""


def allocate(tasks, pools, profiles, budget, seed=0):
    raise NotImplementedError("Build step 7 — see docs/System_Architecture_v2.md §5.2.4")
