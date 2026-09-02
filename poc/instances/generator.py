"""
Synthetic instance generator.

Spec: docs/System_Architecture_v2.md §6.4.
Build step 3. Verified by: instances well-formed; every C(t) non-empty.
Owner: 083 (deliverable D2, due 8 Sep)

    generate(n_tasks, n_profiles, budget_tightness, seed) -> ProblemInstance

budget_tightness ∈ (0, 1] is the PRIMARY EXPERIMENTAL AXIS (T3). The comparison has no
signal where the budget is loose, so this is the knob the sweep turns.

NAMING. §6.4 calls the return value an "Instance", but §5.1 already uses Instance for a
provisioned count {profile_id, count}. Two different things, one word. The problem is a
ProblemInstance here; types.Instance keeps its §5.1 meaning.

INTERPRETATION, worth knowing before reading T3 results. §6.4 defines the budget as "a
fraction of the GPUs needed by a naive one-instance-per-profile solution", which is taken
literally: naive_gpus = Σ_m gpu(m), one instance of every profile in M. That anchor is
arbitrary in the sense that it does not depend on the tasks at all — a batch whose total
load needs three instances of one profile is not served by the "naive" solution. It is
monotone in tightness, which is what the sweep needs, and naive_gpus is exposed on the
result so T3 can sweep absolute B and ignore the anchor entirely. If T3 finds the binding
region sits at odd tightness values, suspect this definition before suspecting the data.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from poc.formulation.types import ProfileSpec, Task, TaskId

MAX_REGENERATION_ATTEMPTS = 100


@dataclass(frozen=True)
class ProblemInstance:
    tasks: list[Task]
    pools: dict[TaskId, list[str]]
    profiles: dict[str, ProfileSpec]
    budget: int
    naive_gpus: int
    seed: int
    budget_tightness: float

    def unpack(self):
        """(tasks, pools, profiles, budget) — the argument order every track takes."""
        return self.tasks, self.pools, self.profiles, self.budget


def _draw_profiles(rng, n_profiles: int) -> dict[str, ProfileSpec]:
    profiles = {}
    for i in range(n_profiles):
        pid = f"m{i + 1}"
        gpus = int(rng.integers(1, 5))
        # Throughput and price both scale with GPUs, with noise, so that no profile is
        # dominated outright and the cheap-small vs expensive-large tradeoff is real.
        throughput = float(np.round(gpus * rng.uniform(8.0, 14.0), 2))
        price = float(np.round(gpus * rng.uniform(80.0, 120.0), 2))
        profiles[pid] = ProfileSpec(
            id=pid,
            declared_type="generic",
            throughput=throughput,
            gpus=gpus,
            price=price,
            reliability=float(np.round(rng.uniform(0.90, 0.999), 3)),
            latency=float(np.round(rng.uniform(20.0, 150.0), 1)),
        )
    return profiles


def _draw_tasks(rng, n_tasks: int, profiles: dict[str, ProfileSpec]) -> list[Task]:
    reliabilities = sorted(p.reliability for p in profiles.values())
    latencies = sorted(p.latency for p in profiles.values())
    tasks = []
    for i in range(n_tasks):
        # Floors are drawn from the profiles' own value range rather than an absolute
        # scale, so a generated instance cannot ask for reliability no profile offers.
        # This makes empty pools rare; the regeneration loop below is the guarantee.
        rel_floor = float(rng.choice(reliabilities))
        lat_ceil = float(rng.choice(latencies))
        tasks.append(Task(
            id=TaskId("wf" + str(int(rng.integers(1, 4))), f"t{i + 1}"),
            task_type="generic",
            load=float(np.round(rng.uniform(1.0, 20.0), 2)),
            rel_floor=rel_floor,
            lat_ceil=lat_ceil,
        ))
    return tasks


def _build_pools(tasks, profiles) -> dict[TaskId, list[str]]:
    """C(t) = { m : rel(m) ≥ R_min(t) and lat(t,m) ≤ L_max(t) } — v2 §1.6."""
    return {
        task.id: sorted(m.id for m in profiles.values()
                        if m.reliability >= task.rel_floor and m.latency <= task.lat_ceil)
        for task in tasks
    }


def generate(n_tasks: int, n_profiles: int, budget_tightness: float,
             seed: int) -> ProblemInstance:
    if not 0.0 < budget_tightness <= 1.0:
        raise ValueError(f"budget_tightness must be in (0, 1], got {budget_tightness}")
    if n_tasks < 1 or n_profiles < 1:
        raise ValueError("n_tasks and n_profiles must be >= 1")

    for attempt in range(MAX_REGENERATION_ATTEMPTS):
        # Derive a distinct stream per attempt so a discarded instance is not simply
        # redrawn identically, while the whole sequence stays a function of `seed` (P10).
        rng = np.random.default_rng([seed, attempt])
        profiles = _draw_profiles(rng, n_profiles)
        tasks = _draw_tasks(rng, n_tasks, profiles)
        pools = _build_pools(tasks, profiles)

        if any(not pool for pool in pools.values()):
            continue        # discard and regenerate — §6.4

        naive_gpus = sum(p.gpus for p in profiles.values())
        budget = max(1, int(round(budget_tightness * naive_gpus)))
        return ProblemInstance(tasks=tasks, pools=pools, profiles=profiles,
                               budget=budget, naive_gpus=naive_gpus, seed=seed,
                               budget_tightness=budget_tightness)

    raise RuntimeError(
        f"could not generate an instance with all pools non-empty in "
        f"{MAX_REGENERATION_ATTEMPTS} attempts (n_tasks={n_tasks}, "
        f"n_profiles={n_profiles}, seed={seed})")
