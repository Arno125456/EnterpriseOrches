"""
Exact reference — direct MILP encoding of §1.4-1.6 in PuLP with CBC.

Spec: docs/System_Architecture_v2.md §5.2.5.
Build step 4 — BEFORE any heuristic.
Verified by: returns 280 on instances/fixtures/adversarial_3t2p.
Owner: 089

Not a track. Ground truth for small-instance testing and the evaluation baseline.

    minimize   Σ_m n[m]·price(m)
    s.t.       (C1)  Σ_{m ∈ C(t)} x[t][m] = 1                       ∀t
               (C2)  Σ_t x[t][m]·load(t)  ≤  n[m]·thr(m)            ∀m
               (C3)  Σ_m n[m]·gpu(m)  ≤  B
               x[t][m] ∈ {0,1},  n[m] ∈ Z⁺

Two things this encoding does NOT do, both deliberate:

  * No linking constraint. If x[t][m]=1 and load(t)>0, (C2) forces n[m] ≥ 1, so an
    explicit x ≤ y would be redundant (v2 §1.6). Note the load(t)>0 caveat is load-bearing:
    a zero-load task would leave n[m] free at 0 and violate I5. The generator draws
    load > 0 and this asserts it rather than trusting it.
  * No floor constraints. Floors are applied when building C(t); x variables only exist
    for eligible pairs, so an ineligible assignment is not representable.

The PuLP + CBC scaffolding follows docs/v1_superseded/offline_baselines/milp_baseline.py,
but not its formulation — that one has no n[m] at all and charges GPUs per task assignment.
"""

from __future__ import annotations

import time

import pulp

from poc.formulation import invariants
from poc.formulation.types import AllocationResult, Infeasible, ProfileSpec, Task, TaskId

STRATEGY = "MILP"


def _instance_upper_bound(profile: ProfileSpec, total_load: float, budget: int) -> int:
    """A finite, valid cap on n[m]. Unbounded integers make CBC work harder than it needs.

    Never provisioning more than covers all load, nor more than the budget can pay for.
    """
    by_load = -(-int(total_load * 100) // int(profile.throughput * 100)) + 1
    by_budget = budget // profile.gpus
    return max(0, min(by_load, by_budget))


def allocate(tasks: list[Task],
             pools: dict[TaskId, list[str]],
             profiles: dict[str, ProfileSpec],
             budget: int,
             seed: int = 0) -> AllocationResult:
    """Solve to proven optimality. seed is accepted for interface parity (P5); CBC is
    deterministic here and does not use it."""
    started = time.perf_counter()

    for task in tasks:
        if not pools.get(task.id):
            return AllocationResult.failure(
                STRATEGY,
                Infeasible("empty candidate pool — registry or floors too strict",
                           task.id, "C1"),
                time.perf_counter() - started)
        if task.load <= 0:
            raise ValueError(
                f"task {task.id} has load {task.load}; the no-linking-constraint argument "
                f"in v2 §1.6 requires load > 0")

    total_load = sum(t.load for t in tasks)
    problem = pulp.LpProblem("TwoLevelAllocation", pulp.LpMinimize)

    x = {(t.id, m): pulp.LpVariable(f"x_{t.id.workflow_id}_{t.id.task_name}_{m}",
                                    cat="Binary")
         for t in tasks for m in pools[t.id]}
    n = {m: pulp.LpVariable(f"n_{m}", lowBound=0,
                            upBound=_instance_upper_bound(p, total_load, budget),
                            cat="Integer")
         for m, p in profiles.items()}

    problem += pulp.lpSum(n[m] * profiles[m].price for m in profiles), "TotalCost"

    for task in tasks:
        problem += (pulp.lpSum(x[(task.id, m)] for m in pools[task.id]) == 1,
                    f"C1_{task.id.workflow_id}_{task.id.task_name}")

    for m in profiles:
        routed = pulp.lpSum(x[(t.id, m)] * t.load for t in tasks if m in pools[t.id])
        problem += (routed <= n[m] * profiles[m].throughput, f"C2_{m}")

    problem += (pulp.lpSum(n[m] * profiles[m].gpus for m in profiles) <= budget, "C3")

    problem.solve(pulp.PULP_CBC_CMD(msg=0))
    elapsed = time.perf_counter() - started
    status = pulp.LpStatus[problem.status]

    if status != "Optimal":
        return AllocationResult.failure(
            STRATEGY,
            Infeasible(f"MILP returned {status} — no allocation fits the GPU budget",
                       None, "C3"),
            elapsed)

    routing = {t.id: m for t in tasks for m in pools[t.id]
               if round(x[(t.id, m)].value() or 0) == 1}
    provisioning = {m: int(round(n[m].value() or 0)) for m in profiles
                    if round(n[m].value() or 0) > 0}
    total_cost = sum(count * profiles[m].price for m, count in provisioning.items())
    gpus_used = sum(count * profiles[m].gpus for m, count in provisioning.items())

    result = AllocationResult(
        routing=routing, provisioning=provisioning,
        total_cost=total_cost, gpus_used=gpus_used,
        strategy=STRATEGY,
        lower_bound=total_cost,     # exact — the bound is the optimum
        compute_time=elapsed, feasible=True,
    )

    violations = invariants.check(result, tasks, pools, profiles, budget)
    if violations:
        # v2 §4.1: verification failure is an internal error. Fail loudly — a MILP that
        # violates its own constraints means the encoding is wrong, not the instance.
        raise RuntimeError(f"exact MILP produced a result violating {violations}")

    return result
