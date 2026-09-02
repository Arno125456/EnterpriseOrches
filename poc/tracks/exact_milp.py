"""
Exact reference — direct MILP encoding of §1.4-1.6 in PuLP with CBC.

Spec: docs/System_Architecture_v2.md §5.2.5.
Build step 4 — BEFORE any heuristic.
Verified by: returns 280 on instances/fixtures/adversarial_3t2p.py.
Owner: 089

Not a track. Ground truth for small-instance testing and the evaluation baseline.

    minimize   Σ_m n[m]·price(m)
    s.t.       (C1)  Σ_{m ∈ C(t)} x[t][m] = 1                       ∀t
               (C2)  Σ_t x[t][m]·load(t)  ≤  n[m]·thr(m)            ∀m
               (C3)  Σ_m n[m]·gpu(m)  ≤  B
               x[t][m] ∈ {0,1},  n[m] ∈ Z⁺

No linking constraint is needed: if x[t][m]=1 and load(t)>0, (C2) forces n[m] ≥ 1
(v2 §1.6). Floors are applied when building C(t), not as constraints.

The PuLP + CBC scaffolding in docs/v1_superseded/offline_baselines/milp_baseline.py is the
pattern to follow — but NOT its formulation, which consumes capacity per task assignment
and has no n[m] at all.
"""


def allocate(tasks, pools, profiles, budget, seed=0):
    raise NotImplementedError("Build step 4 — see docs/System_Architecture_v2.md §5.2.5")
