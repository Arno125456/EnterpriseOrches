"""
The closed loop: J1 -> J2 -> J3 -> J4 -> J5 -> J6 -> J7 -> J8 -> J9 -> J3 ...

Outside PoC scope — see prototype/README.md. Owner: 077.

This is the first place in the repo where the system runs as a system rather than as
components. Every job in §3.1 except J10 participates:

    J1  ingest        prototype/ingestion.py
    J2  resolve       prototype/registry.py
    J3  allocate      poc/tracks/*
    J4  persist       AssignmentRegistry below
    J5  execute       prototype/simulator.py   (simulated — see that module)
    J6  observe       simulator emits Observations
    J7  profile       prototype/profiling.py   ProfileStore
    J8  drift         prototype/profiling.py   DriftDetector
    J9  re-optimise   globally, per F18 — no scoping

WHAT THIS IS FOR

Three questions that only appear when the parts are connected, and that no component test
can ask:

  1. **Does the Profile Store converge?** The registry's declared values are deliberately
     wrong. Measured reliability should approach the hidden truth.
  2. **Does the system thrash?** A drift signal triggers a re-allocation, which changes what
     gets executed, which produces different observations, which can trigger another signal.
     That feedback path is the obvious instability and nothing has ever exercised it.
  3. **Does it respond to a real regime change?** When a profile genuinely degrades, the
     loop should notice and route away from it — and should not do so on noise.

A run returns a `RoundRecord` per round so the trajectory can be inspected rather than only
the endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from poc.formulation.types import AllocationResult, ProfileSpec, Task, TaskId
from prototype.profiling import DriftDetector, ProfileStore
from prototype.registry import ExecutorRegistry, resolve
from prototype.simulator import SimulatedExecutor


@dataclass
class AssignmentRegistry:
    """J4 — persist versioned assignments (§2.3). Append-only; the last is active."""

    versions: list[AllocationResult] = field(default_factory=list)

    def persist(self, result: AllocationResult) -> int:
        if not result.feasible:
            raise ValueError("refusing to persist an infeasible allocation (P9)")
        self.versions.append(result)
        return len(self.versions) - 1

    @property
    def active(self) -> AllocationResult:
        if not self.versions:
            raise ValueError("no assignment has been persisted")
        return self.versions[-1]


@dataclass(frozen=True)
class RoundRecord:
    round_index: int
    routing: dict[TaskId, str]
    cost: float
    measured: dict[str, float]        # profile_id -> measured reliability
    successes: int
    failures: int
    drift_fired: bool
    drift_compatibility: float
    reallocated: bool
    reason: str


def run(batch_tasks: list[Task],
        registry: ExecutorRegistry,
        executor: SimulatedExecutor,
        allocate,
        budget: int,
        rounds: int = 20,
        drift_threshold: float = 0.9,
        min_observations: int = 5) -> list[RoundRecord]:
    """Run the loop for `rounds` execution rounds. Returns one record per round."""
    store = ProfileStore(registry.all_profiles())
    detector = DriftDetector(allocate, threshold=drift_threshold,
                             min_observations=min_observations)
    assignments = AssignmentRegistry()
    records: list[RoundRecord] = []

    def current_pools(profiles: dict[str, ProfileSpec]):
        """J2 against the CURRENT measured profiles, not the declared ones.

        This is what makes the loop closed: as measurement moves reliability, pools shrink
        and grow, and a profile can become ineligible for a task it was serving.
        """
        measured_registry = ExecutorRegistry()
        for spec in profiles.values():
            measured_registry.register(spec)
        return resolve(batch_tasks, measured_registry)

    # --- J2, J3, J4 for the first round -----------------------------------------
    profiles = store.snapshot()
    pools = current_pools(profiles)
    result = allocate(batch_tasks, pools, profiles, budget)
    if not result.feasible:
        return records
    assignments.persist(result)

    for index in range(rounds):
        routing = assignments.active.routing

        # --- J5, J6 ---------------------------------------------------------------
        observations = executor.execute(routing)
        successes = sum(1 for o in observations if o.success)

        # --- J7 -------------------------------------------------------------------
        for observation in observations:
            store.record(observation)
        profiles = store.snapshot()

        # --- J2 again: measurement may have changed eligibility -------------------
        pools = current_pools(profiles)
        starved = [t.id for t in batch_tasks if not pools[t.id]]

        # --- J8 -------------------------------------------------------------------
        if starved:
            signal_fired, compatibility = True, 0.0
            reason = f"{len(starved)} task(s) have no eligible profile under measurement"
        else:
            signal = detector.check(routing, batch_tasks, pools, profiles, budget)
            signal_fired, compatibility, reason = (
                signal.fired, signal.compatibility, signal.reason)

        # --- J9: global re-optimisation, per F18 ----------------------------------
        reallocated = False
        if signal_fired:
            candidate = allocate(batch_tasks, pools, profiles, budget)
            if candidate.feasible:
                assignments.persist(candidate)
                reallocated = True
            else:
                reason += "; re-optimisation infeasible, keeping the previous assignment"

        records.append(RoundRecord(
            round_index=index,
            routing=dict(routing),
            cost=assignments.active.total_cost,
            measured={m: profiles[m].reliability for m in sorted(profiles)},
            successes=successes,
            failures=len(observations) - successes,
            drift_fired=signal_fired,
            drift_compatibility=compatibility,
            reallocated=reallocated,
            reason=reason,
        ))

    return records
