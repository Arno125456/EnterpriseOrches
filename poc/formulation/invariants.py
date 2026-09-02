"""
I1-I5 — asserted on every allocation result, in every test.

Spec: docs/System_Architecture_v2.md §5.1, §6.3.
Build step 2. Verified by: hand-built valid and violating results.
Owner: 083

    I1  every task appears exactly once in routing                    (C1)
    I2  for every m: Σ load routed to m  ≤  n[m] · thr(m)             (C2)
    I3  Σ n[m] · gpu(m)  ≤  B                                          (C3)
    I4  every routed profile is in C(t) for its task                  (floors)
    I5  n[m] ≥ 1 for every profile appearing in routing

All three tracks have relaxation or rounding steps that can silently emit violating
results. This is the single highest-value piece of test infrastructure in the PoC —
wire it in at step 2 and call it everywhere (CLAUDE.md).
"""


def check(result, tasks, pools, profiles, budget):
    """Return a list of violated invariant IDs. Empty list means valid.

    Called by every test and by the harness on every produced result.
    """
    raise NotImplementedError("Build step 2 — see docs/System_Architecture_v2.md §6.3")
