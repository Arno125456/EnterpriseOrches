"""
Tracks vs the exact optimum by exhaustion, on instances small enough to enumerate.

Spec: docs/System_Architecture_v2.md §6.6 (component + bound levels).
Covers build step 4 now; steps 7-9 as the tracks land. Owner: 089

The brute-force optimum here is independent of PuLP, so this is a real check on the MILP
encoding rather than the solver agreeing with itself. Everything else in the PoC is
measured against the MILP, so if the encoding is wrong, every later result is wrong
quietly.
"""

import itertools
import math

import pytest

from poc.formulation import invariants
from poc.instances.generator import generate
from poc.tracks import exact_milp


def brute_force(tasks, pools, profiles, budget):
    """Enumerate every routing. Returns (cost, routing) or (None, None) if infeasible."""
    best_cost, best_routing = None, None
    task_ids = [t.id for t in tasks]
    load_of = {t.id: t.load for t in tasks}

    for combo in itertools.product(*[pools[tid] for tid in task_ids]):
        routing = dict(zip(task_ids, combo))
        load = {}
        for tid, m in routing.items():
            load[m] = load.get(m, 0.0) + load_of[tid]
        n = {m: math.ceil(round(l / profiles[m].throughput, 9)) for m, l in load.items()}
        gpus = sum(c * profiles[m].gpus for m, c in n.items())
        if gpus > budget:
            continue
        cost = sum(c * profiles[m].price for m, c in n.items())
        if best_cost is None or cost < best_cost - 1e-9:
            best_cost, best_routing = cost, routing

    return best_cost, best_routing


@pytest.mark.parametrize("seed", range(12))
@pytest.mark.parametrize("tightness", [0.35, 0.6, 1.0])
def test_milp_matches_brute_force(seed, tightness):
    inst = generate(n_tasks=6, n_profiles=3, budget_tightness=tightness, seed=seed)
    tasks, pools, profiles, budget = inst.unpack()

    expected_cost, _ = brute_force(tasks, pools, profiles, budget)
    result = exact_milp.allocate(tasks, pools, profiles, budget)

    if expected_cost is None:
        assert not result.feasible, "brute force found nothing; MILP claims a solution"
        assert result.infeasible.constraint == "C3"
        return

    assert result.feasible, f"brute force found {expected_cost}; MILP reported infeasible"
    assert result.total_cost == pytest.approx(expected_cost), (
        f"MILP {result.total_cost} != exhaustive optimum {expected_cost}")
    assert invariants.check(result, tasks, pools, profiles, budget) == []


@pytest.mark.parametrize("seed", range(5))
def test_milp_result_is_internally_consistent(seed):
    """Reported cost and GPUs must follow from the provisioning it returns."""
    inst = generate(n_tasks=7, n_profiles=4, budget_tightness=0.7, seed=seed)
    tasks, pools, profiles, budget = inst.unpack()
    result = exact_milp.allocate(tasks, pools, profiles, budget)
    if not result.feasible:
        pytest.skip("infeasible at this tightness")

    assert result.total_cost == pytest.approx(
        sum(c * profiles[m].price for m, c in result.provisioning.items()))
    assert result.gpus_used == sum(
        c * profiles[m].gpus for m, c in result.provisioning.items())
    assert result.gpus_used <= budget


def test_infeasible_names_the_binding_constraint():
    """A budget too small for any allocation must be reported, not crashed on (§4.1)."""
    inst = generate(n_tasks=6, n_profiles=3, budget_tightness=1.0, seed=2)
    tasks, pools, profiles, _ = inst.unpack()
    result = exact_milp.allocate(tasks, pools, profiles, budget=1)

    if result.feasible:
        pytest.skip("budget=1 happens to be satisfiable for this instance")
    assert result.infeasible.constraint == "C3"
    assert not result.routing and not result.provisioning
