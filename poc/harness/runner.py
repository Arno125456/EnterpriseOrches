"""
Run all conditions under matched inputs.

Spec: docs/System_Architecture_v2.md §4.7.
Build step 10. Owner: 089

Matched conditions are not a detail. Any condition this project introduces that Murakkab's
evaluation did not use requires the MILP baseline to be re-run under it before an
improvement is claimed (v2 §4.7). That is why every condition here is handed the identical
instance object rather than regenerating from the seed per track — a generator change
mid-run would otherwise compare tracks against different problems and nobody would notice.

Determinism: every track takes seed; randomised orderings derive from it, so runs reproduce
exactly (principle P10).

WHAT IS NOT HERE. §4.7 lists five conditions: Tracks A, B, C, a static baseline, and the
exact MILP. The registry names what it is not running, out loud, so a partial run never
passes itself off as the full set:

    MURAKKAB  not separate — the §1 formulation is Murakkab's model, so the MILP
              condition IS the Murakkab baseline (see static_baseline.py)

Track B relaxes (C1) on §1.8's prediction rather than on a T1 result. That assumption is
documented in track_b_lagr.py; the harness records its bound so T1 can be read off it.

A+M1 is a condition §4.7 does not list. It is the M1 analogue T4's table calls for, kept
separate from A so the machinery can be priced rather than assumed (see track_a_m1.py).

`invariants.check` runs on every result before it is recorded, per §6.6.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from poc.formulation import invariants
from poc.formulation.types import AllocationResult
from poc.instances.generator import ProblemInstance, generate
from poc.tracks import (exact_milp, static_baseline, track_a_greedy,
                        track_a_m1, track_b_lagr, track_c_lp,
                        track_c_multi)

# Condition name -> module exposing allocate(tasks, pools, profiles, budget, seed).
STRATEGIES = {
    "MILP": exact_milp,          # also the Murakkab condition — see UNAVAILABLE["MURAKKAB"]
    "STATIC": static_baseline,
    "A": track_a_greedy,
    "A+M1": track_a_m1,
    "B": track_b_lagr,
    "C": track_c_lp,
    "C2": track_c_multi,
}

# Named, with the reason, so a run's output can state what it did not measure.
UNAVAILABLE = {
    "MURAKKAB": ("not a separate condition — §1's formulation IS Murakkab's model, so "
                 "re-running Murakkab under matched conditions means running MILP. A "
                 "second entry would report the same number twice"),
}


@dataclass(frozen=True)
class ConditionResult:
    condition: str
    result: AllocationResult
    violations: list[str]

    @property
    def feasible(self) -> bool:
        return self.result.feasible

    @property
    def cost(self) -> float | None:
        return self.result.total_cost if self.result.feasible else None


@dataclass(frozen=True)
class RunRecord:
    """One instance, every condition, under matched inputs."""

    instance: ProblemInstance
    conditions: dict[str, ConditionResult]
    optimum: float | None
    wall_time: float = 0.0

    @property
    def solvable(self) -> bool:
        """Whether the exact solver found anything. Nothing else is interpretable if not."""
        return self.optimum is not None


def run_conditions(instance: ProblemInstance,
                   strategies: list[str] | None = None,
                   seed: int = 0) -> RunRecord:
    """Run every named condition against one instance, with identical inputs."""
    names = list(STRATEGIES) if strategies is None else list(strategies)
    unknown = [n for n in names if n not in STRATEGIES]
    if unknown:
        detail = "; ".join(f"{n}: {UNAVAILABLE[n]}" for n in unknown if n in UNAVAILABLE)
        raise ValueError(f"unknown condition(s) {unknown}. {detail or 'check STRATEGIES'}")

    tasks, pools, profiles, budget = instance.unpack()
    started = time.perf_counter()
    conditions: dict[str, ConditionResult] = {}

    for name in names:
        result = STRATEGIES[name].allocate(tasks, pools, profiles, budget, seed=seed)
        conditions[name] = ConditionResult(
            condition=name,
            result=result,
            violations=invariants.check(result, tasks, pools, profiles, budget),
        )

    optimum = None
    if "MILP" in conditions and conditions["MILP"].feasible:
        optimum = conditions["MILP"].result.total_cost

    return RunRecord(instance=instance, conditions=conditions, optimum=optimum,
                     wall_time=time.perf_counter() - started)


def sweep(n_tasks: int,
          n_profiles: int,
          tightness_values,
          seeds,
          strategies: list[str] | None = None) -> list[RunRecord]:
    """The T3 sweep: budget tightness across a fixed set of instances.

    T3 asks where the budget binds, so the axis is tightness and everything else is held
    fixed. Note the same `seed` produces the same tasks and profiles at every tightness —
    only B moves — which is what makes the sweep a sweep rather than a set of unrelated
    instances.
    """
    records = []
    for tightness in tightness_values:
        for seed in seeds:
            instance = generate(n_tasks=n_tasks, n_profiles=n_profiles,
                                budget_tightness=tightness, seed=seed)
            records.append(run_conditions(instance, strategies))
    return records


def main() -> None:
    """Reproduce the sweep recorded in docs/poc_findings.md.

    Deliberately hard-coded rather than argparse'd: the point is that the numbers in the
    findings log can be regenerated by one command with no arguments to get wrong.
    """
    from poc.harness import metrics

    tightness = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    records = sweep(n_tasks=8, n_profiles=4, tightness_values=tightness, seeds=range(25))

    print(f"{len(records)} instances — 8 tasks, 4 profiles, seeds 0-24, "
          f"tightness {tightness}")
    print(f"conditions run: {', '.join(STRATEGIES)}")
    for name, why in UNAVAILABLE.items():
        print(f"  not run — {name}: {why}")

    print("\nT3 view — solvability by budget tightness")
    for value, (ok, total) in metrics.solvability(records).items():
        print(f"  {value:>4}  {ok:>3}/{total}  {'#' * ok}")

    print("\nT4 view — all conditions, over solvable instances only")
    print(metrics.format_table(metrics.summarise(records)))

    offenders = [(r.instance.seed, name, c.violations)
                 for r in records for name, c in r.conditions.items() if c.violations]
    print(f"\ninvariant violations: {offenders or 'none'}")


if __name__ == "__main__":
    main()
