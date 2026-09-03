"""
A heterogeneous-fleet instance generator, resolving O13 and Finding F31.

Spec: docs/poc_findings.md §F31.
Owner: 083 / 089

WHY THIS EXISTS (FINDING F31 / OPEN QUESTION O13)

Both generator.py and structured_generator.py assume price scales roughly as
gpus * U(80, 120), encoding a homogeneous fleet where corr(price, gpus) ≈ 0.95–1.0.
Under that assumption, minimizing cost and minimizing GPU usage are nearly identical
axes, causing Finding F26 ("the GPU budget constraint C3 is nearly inert").

As proved in Finding F31 from Murakkab's published numbers (OSDI '26), real enterprise
fleets run heterogeneous GPU architectures (e.g. Commodity T4/L4, Standard A100, Premium
H100) where price-per-GPU and throughput-per-GPU diverge significantly:
  - Video-QA + CodeGen: GPUs fall 2.82x while dollar cost falls 4.33x; cost per GPU
    moves to 0.65x between configurations.
  - Math-QA + CodeGen: cost per GPU moves to 0.76x.

This generator models three distinct hardware tiers:
  1. Commodity (e.g., T4/L4): Low price/GPU ($30-$50), low throughput/GPU (4-7), higher latency.
  2. Standard (e.g., A100): Balanced price/GPU ($90-$130), high throughput/GPU (12-18).
  3. Premium (e.g., H100): High price/GPU ($240-$360), ultra-high throughput/GPU (35-55), lowest latency.

Under this heterogeneous structure:
  - corr(price, gpus) is decoupled (typically 0.3–0.6).
  - High-end GPUs provide high throughput density (low gpus/throughput), which is
    essential when the GPU budget B is tight.
  - Lower-tier GPUs provide cheap throughput capacity, which is cost-optimal when
    the GPU budget B is loose.
  - Constraint (C3) actively couples with (C2) and directly shapes the cost optimum.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from poc.formulation.types import ProfileSpec, Task, TaskId
from poc.instances.generator import (MAX_REGENERATION_ATTEMPTS, ProblemInstance,
                                     _build_pools, _reference_gpus)

# Hardware tiers: (name, gpu_options, throughput_per_gpu_range, price_per_gpu_range, latency_range, rel_range)
HARDWARE_TIERS = [
    ("commodity", (2, 4), (4.0, 7.0), (30.0, 50.0), (70.0, 150.0), (0.90, 0.97)),
    ("standard", (1, 2, 4), (12.0, 18.0), (90.0, 130.0), (30.0, 80.0), (0.95, 0.99)),
    ("premium", (1, 2), (35.0, 55.0), (240.0, 360.0), (10.0, 40.0), (0.98, 0.999)),
]


def _draw_profiles(rng, n_profiles: int) -> dict[str, ProfileSpec]:
    profiles = {}
    for i in range(n_profiles):
        # Round-robin or uniformly select hardware tier so every instance has heterogeneity
        tier_idx = i % len(HARDWARE_TIERS)
        name, gpu_opts, thr_range, price_range, lat_range, rel_range = HARDWARE_TIERS[tier_idx]

        gpus = int(gpu_opts[rng.integers(0, len(gpu_opts))])
        throughput = float(np.round(gpus * rng.uniform(*thr_range), 2))
        price = float(np.round(gpus * rng.uniform(*price_range), 2))
        latency = float(np.round(rng.uniform(*lat_range), 1))
        reliability = float(np.round(rng.uniform(*rel_range), 3))

        pid = f"m{i + 1}"
        profiles[pid] = ProfileSpec(
            id=pid,
            declared_type=name,
            throughput=throughput,
            gpus=gpus,
            price=price,
            reliability=reliability,
            latency=latency,
        )
    return profiles


def _draw_tasks(rng, n_tasks: int, profiles: dict[str, ProfileSpec]) -> list[Task]:
    reliabilities = sorted(p.reliability for p in profiles.values())
    latencies = sorted(p.latency for p in profiles.values())
    tasks = []
    for i in range(n_tasks):
        rel_floor = float(rng.choice(reliabilities))
        lat_ceil = float(rng.choice(latencies))
        load = float(np.round(rng.uniform(2.0, 30.0), 2))
        tasks.append(Task(
            id=TaskId("wf" + str(int(rng.integers(1, 4))), f"t{i + 1}"),
            task_type="generic",
            load=load,
            rel_floor=rel_floor,
            lat_ceil=lat_ceil,
        ))
    return tasks


def generate(n_tasks: int, n_profiles: int, budget_tightness: float,
             seed: int) -> ProblemInstance:
    """Generate a reproducible heterogeneous-fleet problem instance.

    Guarantees:
      - Every task has a non-empty candidate pool C(t) != empty.
      - At budget_tightness >= 1.0, the instance is feasible by construction.
      - price and gpus have distinct, tier-dependent scaling ratios.
    """
    if not (0.0 < budget_tightness <= 3.0):
        raise ValueError(f"budget_tightness must be in (0.0, 3.0], got {budget_tightness}")

    rng = np.random.default_rng(seed)

    for _ in range(MAX_REGENERATION_ATTEMPTS):
        profiles = _draw_profiles(rng, n_profiles)
        tasks = _draw_tasks(rng, n_tasks, profiles)
        pools = _build_pools(tasks, profiles)
        if all(pools[t.id] for t in tasks):
            ref_gpus = _reference_gpus(tasks, pools, profiles)
            budget = max(1, int(round(ref_gpus * budget_tightness)))
            return ProblemInstance(
                tasks=tasks,
                pools=pools,
                profiles=profiles,
                budget=budget,
                reference_gpus=ref_gpus,
                seed=seed,
                budget_tightness=budget_tightness,
            )

    raise RuntimeError(
        f"Failed to draw a valid heterogeneous instance in {MAX_REGENERATION_ATTEMPTS} attempts (seed={seed})"
    )
