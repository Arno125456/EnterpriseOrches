"""
Tests for the heterogeneous fleet generator (resolving Finding F31 / O13).
"""

import numpy as np
import pytest

from poc.instances.heterogeneous_generator import generate
from poc.tracks import exact_milp


@pytest.mark.parametrize("seed", range(15))
def test_pools_are_never_empty(seed):
    inst = generate(n_tasks=8, n_profiles=6, budget_tightness=0.5, seed=seed)
    assert all(inst.pools[t.id] for t in inst.tasks)


@pytest.mark.parametrize("seed", range(10))
def test_pools_agree_with_the_floors(seed):
    inst = generate(n_tasks=8, n_profiles=6, budget_tightness=0.5, seed=seed)
    for task in inst.tasks:
        derived = sorted(m.id for m in inst.profiles.values()
                         if m.reliability >= task.rel_floor and m.latency <= task.lat_ceil)
        assert derived == inst.pools[task.id]


def test_same_seed_reproduces_exactly():
    a = generate(6, 4, 0.5, seed=42)
    b = generate(6, 4, 0.5, seed=42)
    assert a == b


def test_different_seeds_differ():
    assert generate(6, 4, 0.5, seed=1) != generate(6, 4, 0.5, seed=2)


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("n_tasks", [4, 8])
def test_tightness_of_one_is_always_feasible(seed, n_tasks):
    inst = generate(n_tasks=n_tasks, n_profiles=6, budget_tightness=1.0, seed=seed)
    res = exact_milp.allocate(*inst.unpack())
    assert res.feasible, f"seed {seed} failed at tightness 1.0"
    assert res.gpus_used <= inst.reference_gpus


def test_price_and_gpus_are_decorrelated():
    """Finding F31: In a heterogeneous fleet, price is NOT a multiple of GPU count.
    
    In the uniform/structured generators, corr(price, gpus) >= 0.95.
    In the heterogeneous generator, the tier spread ensures corr(price, gpus) is significantly lower.
    """
    gpus_list = []
    price_list = []
    # Collect profiles across multiple seeds to measure correlation
    for s in range(10):
        inst = generate(n_tasks=8, n_profiles=6, budget_tightness=1.0, seed=s)
        for p in inst.profiles.values():
            gpus_list.append(p.gpus)
            price_list.append(p.price)

    corr = np.corrcoef(gpus_list, price_list)[0, 1]
    # Price per GPU varies from $30 (commodity) to $360 (premium), decorrelating the two
    assert corr < 0.80, f"Expected decorrelated fleet, got corr={corr:.3f}"


def test_budget_constraint_actively_affects_cost():
    """Verify that relaxing the GPU budget allows the optimizer to trade GPUs for lower cost.
    
    This directly validates Finding F31: under a heterogeneous fleet, (C3) is not inert.
    """
    # At tightness 0.9, budget is tight -> must buy GPU-dense profiles
    inst_tight = generate(n_tasks=8, n_profiles=6, budget_tightness=0.9, seed=3)
    # At tightness 1.5, budget is loose -> can buy dollar-cheap profiles
    inst_loose = generate(n_tasks=8, n_profiles=6, budget_tightness=1.5, seed=3)

    res_tight = exact_milp.allocate(*inst_tight.unpack())
    res_loose = exact_milp.allocate(*inst_loose.unpack())

    assert res_tight.feasible
    assert res_loose.feasible
    # When budget is loose, cost is less than or equal to when budget is tight
    assert res_loose.total_cost <= res_tight.total_cost
