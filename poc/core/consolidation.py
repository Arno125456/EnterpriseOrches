"""
A multi-move neighbourhood: relocate every task on one profile to another, together.

Spec: not in any document. Built from a diagnosed failure (findings F17).
Owner: 035 / 075 — it applies to both Track A and Track C.

WHAT IT FIXES

Both the LP relaxation and greedy construction can leave a large profile carrying far less
load than it can hold, because both price a profile by its *rate* — cost per unit of
throughput — while an integer allocation pays for whole instances. A profile with the best
price/throughput ratio can be the worst choice if the load routed to it fills a fraction of
one instance.

The diagnosed case (F17): the LP routed 7.88 units of load to a 4-GPU profile at 401.74
because its price/throughput was 11.98, against a 2-GPU profile's 12.79. Fractionally that
is correct — 0.235 instances is cheaper than 0.506. Integrally it wastes 76% of a large
instance and costs twice the optimum.

WHY SINGLE-MOVE RELOCATE CANNOT FIX IT

Moving one task off the underused profile leaves the instance open and still paid for, so
the move saves nothing and usually costs something at the destination. Every single-move
neighbourhood therefore sees a local optimum. The improving move is to relocate *all* of a
profile's tasks at once, which closes the instance and recovers its whole price.

This is the same shape as the fixture in instances/fixtures/adversarial_3t2p.py, where the
improving move is t1 and t2 *together* and CLAUDE.md records by exhaustion that multi-start
plus single-move relocate is provably insufficient. That fixture and this failure are the
same phenomenon seen from opposite ends — one where consolidating is right, one where
de-consolidating is.

SCOPE NOTE

v2 §6.5 defers Track A's relocate/consolidate to T4. This lives in core/ and is wired into
a separate condition rather than into any track, so T4 can still price it. Nothing that
exists today changes behaviour because of this file.
"""

from __future__ import annotations

import math

from poc.formulation.types import ProfileSpec, Task, TaskId

_ROUND_DP = 9


def evaluate(routing: dict[TaskId, str],
             tasks: list[Task],
             profiles: dict[str, ProfileSpec],
             budget: int):
    """(cost, gpus, provisioning) for a routing, or None if it breaks the budget."""
    load: dict[str, float] = {}
    load_of = {t.id: t.load for t in tasks}
    for task_id, profile_id in routing.items():
        load[profile_id] = load.get(profile_id, 0.0) + load_of[task_id]

    provisioning = {m: math.ceil(round(v / profiles[m].throughput, _ROUND_DP))
                    for m, v in load.items() if v > 0}
    gpus = sum(n * profiles[m].gpus for m, n in provisioning.items())
    if gpus > budget:
        return None
    cost = sum(n * profiles[m].price for m, n in provisioning.items())
    return cost, gpus, provisioning


class ConsolidationState:
    """Maintains active profile loads, instance counts, spare headroom, and aggregate costs.

    Provides O(1) evaluation of candidate relocation moves using memoized instance headroom,
    reducing move evaluation from O(|T|) full-fleet recomputations to O(1) scalar arithmetic.
    """

    def __init__(self,
                 routing: dict[TaskId, str],
                 tasks: list[Task],
                 profiles: dict[str, ProfileSpec],
                 budget: int):
        self.profiles = profiles
        self.budget = budget
        self.by_id = {t.id: t for t in tasks}
        self.routing = dict(routing)
        self.load: dict[str, float] = {m: 0.0 for m in profiles}
        for tid, m in self.routing.items():
            self.load[m] += self.by_id[tid].load

        self.provisioning: dict[str, int] = {}
        self.headroom: dict[str, float] = {}
        self.total_gpus: int = 0
        self.total_cost: float = 0.0

        for m, v in self.load.items():
            if v > 1e-9:
                n = math.ceil(round(v / profiles[m].throughput, _ROUND_DP))
                self.provisioning[m] = n
                self.total_gpus += n * profiles[m].gpus
                self.total_cost += n * profiles[m].price
                self.headroom[m] = n * profiles[m].throughput - v
            else:
                self.provisioning[m] = 0
                self.headroom[m] = 0.0

    @property
    def is_feasible(self) -> bool:
        return self.total_gpus <= self.budget

    def evaluate_move(self, movers: tuple[TaskId, ...] | list[TaskId], destination: str) -> tuple[float, int] | None:
        """Evaluates moving `movers` from their source profile to `destination` in O(1).

        Returns (new_total_cost, new_total_gpus) if feasible (<= budget), else None.
        """
        source = self.routing[movers[0]]
        if destination == source:
            return self.total_cost, self.total_gpus

        delta_load = sum(self.by_id[tid].load for tid in movers)
        new_ls = self.load[source] - delta_load
        new_ns = math.ceil(round(new_ls / self.profiles[source].throughput, _ROUND_DP)) if new_ls > 1e-9 else 0
        new_ld = self.load[destination] + delta_load
        new_nd = math.ceil(round(new_ld / self.profiles[destination].throughput, _ROUND_DP))

        delta_gpus = ((new_ns - self.provisioning.get(source, 0)) * self.profiles[source].gpus +
                      (new_nd - self.provisioning.get(destination, 0)) * self.profiles[destination].gpus)

        new_gpus = self.total_gpus + delta_gpus
        if new_gpus > self.budget:
            return None

        delta_cost = ((new_ns - self.provisioning.get(source, 0)) * self.profiles[source].price +
                      (new_nd - self.provisioning.get(destination, 0)) * self.profiles[destination].price)

        return self.total_cost + delta_cost, new_gpus

    def apply_move(self, movers: tuple[TaskId, ...] | list[TaskId], destination: str) -> None:
        """Applies the move, updating routing, loads, provisioning, headroom, cost, and gpus."""
        source = self.routing[movers[0]]
        delta_load = sum(self.by_id[tid].load for tid in movers)

        for tid in movers:
            self.routing[tid] = destination

        # Update source
        new_ls = max(0.0, self.load[source] - delta_load)
        self.load[source] = new_ls
        old_ns = self.provisioning.get(source, 0)
        new_ns = math.ceil(round(new_ls / self.profiles[source].throughput, _ROUND_DP)) if new_ls > 1e-9 else 0
        self.provisioning[source] = new_ns
        self.headroom[source] = (new_ns * self.profiles[source].throughput - new_ls) if new_ns > 0 else 0.0

        # Update destination
        new_ld = self.load[destination] + delta_load
        self.load[destination] = new_ld
        old_nd = self.provisioning.get(destination, 0)
        new_nd = math.ceil(round(new_ld / self.profiles[destination].throughput, _ROUND_DP))
        self.provisioning[destination] = new_nd
        self.headroom[destination] = new_nd * self.profiles[destination].throughput - new_ld

        self.total_gpus += ((new_ns - old_ns) * self.profiles[source].gpus +
                            (new_nd - old_nd) * self.profiles[destination].gpus)
        self.total_cost += ((new_ns - old_ns) * self.profiles[source].price +
                            (new_nd - old_nd) * self.profiles[destination].price)


def consolidate(routing: dict[TaskId, str],
                tasks: list[Task],
                pools: dict[TaskId, list[str]],
                profiles: dict[str, ProfileSpec],
                budget: int,
                max_passes: int = 8) -> dict[TaskId, str]:
    """Repeatedly move all tasks on one profile to another, keeping strict improvements.

    Deterministic: profiles and destinations are tried in sorted order, and only strict
    improvements are accepted, so no cycling and no dependence on dict ordering (P10).

    Complexity: O(passes · |M|² · |T|) worst-case, with O(1) candidate checks via headroom cache.
    """
    state = ConsolidationState(routing, tasks, profiles, budget)
    if not state.is_feasible:
        return routing

    by_id = state.by_id

    for _ in range(max_passes):
        improved = False

        for source in sorted({m for m in state.routing.values()}):
            movers = sorted((tid for tid, m in state.routing.items() if m == source),
                            key=lambda tid: (by_id[tid].id.workflow_id,
                                             by_id[tid].id.task_name))
            if not movers:
                continue

            # A destination must be eligible for every task being moved.
            eligible = sorted(set.intersection(
                *(set(pools[tid]) for tid in movers)) - {source})

            for destination in eligible:
                outcome = state.evaluate_move(movers, destination)
                if outcome is not None and outcome[0] < state.total_cost - 1e-9:
                    state.apply_move(movers, destination)
                    improved = True
                    break

            if improved:
                break

        if not improved:
            break

    return state.routing


def consolidate_subsets(routing: dict[TaskId, str],
                        tasks: list[Task],
                        pools: dict[TaskId, list[str]],
                        profiles: dict[str, ProfileSpec],
                        budget: int,
                        max_k: int = 2,
                        max_passes: int = 8) -> dict[TaskId, str]:
    """Repeatedly move all tasks, or subsets of up to max_k tasks, from one profile to another.

    Extends consolidate() to multi-move subset neighborhoods. This directly closes the
    aggregate-coupling gap diagnosed on instances/fixtures/adversarial_3t2p.py, where
    moving all tasks is blocked by an ineligible tail task, but moving a subset of tasks
    together opens an instance on an efficient profile with lower aggregate cost.

    Deterministic: candidates and destinations are explored in sorted order; strict
    improvements only (P10).
    """
    import itertools

    state = ConsolidationState(routing, tasks, profiles, budget)
    if not state.is_feasible:
        return routing

    by_id = state.by_id

    for _ in range(max_passes):
        improved = False

        # First, run the full-profile consolidation pass
        routing_after_all = consolidate(state.routing, tasks, pools, profiles, budget, max_passes=1)
        if routing_after_all != state.routing:
            state = ConsolidationState(routing_after_all, tasks, profiles, budget)
            improved = True
            continue

        # Next, search for subset moves of size k in [max_k, ..., 2, 1]
        for k in range(max_k, 0, -1):
            for source in sorted({m for m in state.routing.values()}):
                movers = sorted((tid for tid, m in state.routing.items() if m == source),
                                key=lambda tid: (by_id[tid].id.workflow_id,
                                                 by_id[tid].id.task_name))
                if len(movers) < k:
                    continue

                for subset in itertools.combinations(movers, k):
                    eligible = sorted(set.intersection(
                        *(set(pools[tid]) for tid in subset)) - {source})
                    if not eligible:
                        continue

                    for destination in eligible:
                        outcome = state.evaluate_move(subset, destination)
                        if outcome is not None and outcome[0] < state.total_cost - 1e-9:
                            state.apply_move(subset, destination)
                            improved = True
                            break

                    if improved:
                        break
                if improved:
                    break
            if improved:
                break

        if not improved:
            break

    return state.routing

