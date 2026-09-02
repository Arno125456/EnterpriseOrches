"""
Track C — LP relaxation + rounding.

Spec: docs/System_Architecture_v2.md §5.2.4.
Build step 7. Verified by: bound <= MILP optimum; result satisfies I1-I5.
Owner: 075

Solve with x[t][m] in [0,1] and n[m] >= 0 continuous, keep the LP objective as a valid
lower bound, then round the routing and repair it into feasibility.

Rounding is not incidental here. The LP returns fractional n[m]. Rounding down breaks (C2);
rounding up may break (C3); and rounding one profile up changes headroom that affects
whether another profile's rounding is feasible. It is an algorithm, not a policy switch.

O6 IS NOT SETTLED, AND THIS IS NOT THE ANSWER.

The policy implemented here is the obvious default, chosen so the track could be built and
its bound measured — not because it was compared against alternatives:

    route each task to the profile carrying its largest fractional x[t][m],
    ties broken on profile id; then repair any task whose choice no longer fits.

Tasks are repaired in decreasing load order, on the reasoning that the large tasks are the
ones that force new instances, so placing them while the budget still has room leaves the
small ones something to slot into. That is a guess, not a result. Alternatives nobody has
tried yet: rounding n first and fitting routing to it, LP-guided randomised rounding, or
repairing in LP-confidence order. T3/T4 resolve this — until then treat Track C's cost as
a function of an arbitrary choice, while its BOUND is solid and policy-independent.
"""

from __future__ import annotations

import time

import pulp

from poc.core.decision_rule import select_profile
from poc.core.provisioning import ProvisioningState
from poc.formulation import invariants
from poc.formulation.types import AllocationResult, Infeasible, ProfileSpec, Task, TaskId

STRATEGY = "C"


def _marginal_cost(profile_id: str, admit) -> float:
    return admit.extra_cost


def _solve_relaxation(tasks, pools, profiles, budget):
    """Return (fractional_x, bound) or (None, None) if the LP itself is infeasible."""
    problem = pulp.LpProblem("TwoLevelAllocation_LP", pulp.LpMinimize)

    x = {(t.id, m): pulp.LpVariable(
            f"x_{t.id.workflow_id}_{t.id.task_name}_{m}", lowBound=0, upBound=1,
            cat="Continuous")
         for t in tasks for m in pools[t.id]}
    n = {m: pulp.LpVariable(f"n_{m}", lowBound=0, cat="Continuous") for m in profiles}

    problem += pulp.lpSum(n[m] * profiles[m].price for m in profiles), "TotalCost"

    for task in tasks:
        problem += (pulp.lpSum(x[(task.id, m)] for m in pools[task.id]) == 1,
                    f"C1_{task.id.workflow_id}_{task.id.task_name}")
    for m in profiles:
        routed = pulp.lpSum(x[(t.id, m)] * t.load for t in tasks if m in pools[t.id])
        problem += (routed <= n[m] * profiles[m].throughput, f"C2_{m}")
    problem += (pulp.lpSum(n[m] * profiles[m].gpus for m in profiles) <= budget, "C3")

    problem.solve(pulp.PULP_CBC_CMD(msg=0))
    if pulp.LpStatus[problem.status] != "Optimal":
        return None, None

    fractional = {key: (var.value() or 0.0) for key, var in x.items()}
    return fractional, pulp.value(problem.objective)


def _round_routing(tasks, pools, fractional) -> dict[TaskId, str]:
    """O6's default: argmax fractional weight, ties broken on profile id.

    Expressed as a min over (-weight, id) so the id tie-break is a plain string compare —
    ties are the common case when the LP splits a task evenly.
    """
    return {
        task.id: min(pools[task.id],
                     key=lambda m: (-fractional.get((task.id, m), 0.0), m))
        for task in tasks
    }


def allocate(tasks: list[Task],
             pools: dict[TaskId, list[str]],
             profiles: dict[str, ProfileSpec],
             budget: int,
             seed: int = 0) -> AllocationResult:
    """seed is accepted for interface parity (P5); this track is deterministic."""
    started = time.perf_counter()

    for task in tasks:
        if not pools.get(task.id):
            return AllocationResult.failure(
                STRATEGY,
                Infeasible("empty candidate pool — registry or floors too strict",
                           task.id, "C1"),
                time.perf_counter() - started)

    fractional, bound = _solve_relaxation(tasks, pools, profiles, budget)
    if fractional is None:
        # The LP is a relaxation: if it is infeasible, so is the integer problem.
        return AllocationResult.failure(
            STRATEGY,
            Infeasible("LP relaxation infeasible — no allocation fits the GPU budget",
                       None, "C3"),
            time.perf_counter() - started)

    rounded = _round_routing(tasks, pools, fractional)
    state = ProvisioningState(profiles, budget)
    routing: dict[TaskId, str] = {}

    # Large tasks first: they are the ones that force new instances.
    for task in sorted(tasks, key=lambda t: (-t.load, t.id)):
        choice = rounded[task.id]
        if state.cost_to_admit(task, choice) is None:
            choice = select_profile(task, pools[task.id], state, _marginal_cost)
        if choice is None:
            return AllocationResult.failure(
                STRATEGY,
                Infeasible("rounding repair failed — no profile admissible within budget",
                           task.id, "C3"),
                time.perf_counter() - started)
        state.admit(task, choice)
        routing[task.id] = choice

    result = AllocationResult(
        routing=routing,
        provisioning=state.build_provisioning(),
        total_cost=state.total_cost(),
        gpus_used=state.gpus_used(),
        strategy=STRATEGY,
        lower_bound=bound,
        compute_time=time.perf_counter() - started,
        feasible=True,
    )

    violations = invariants.check(result, tasks, pools, profiles, budget)
    if violations:
        # v2 §4.1: verification failure is an internal error. Never emit a violating
        # assignment — repair returns Infeasible instead.
        raise RuntimeError(f"Track C produced a result violating {violations}")

    return result
