"""
Profile Store with EMA updates, and a Drift Detector (§4.5).

Outside PoC scope — see prototype/README.md. Owner: 077.

This is the half of the project that carries its novelty. "Profile-guided" is the first
phrase in the title, principle P6 is *profiles are measured, not declared*, and R4 is the
requirement none of the PoC touches. It is also the half with no implementation, so this
exists to make the loop concrete enough to argue about.

Nothing here needs an Execution Engine. Observations are fed in directly, which is enough
to exercise the EMA, the drift signal, and the re-optimisation trigger.

THE COMPATIBILITY SCORE IS [PROPOSED] AND IS NOT THE PAPER'S.

§9 attributes it to Hatherley (2025), which is not in this repo. §4.5 describes the
mechanism — "recomputes the would-be decision under the updated profile, computes the
compatibility score, compares to threshold" — but not the score. The definition here is
invented to match that description:

    compatibility = (tasks whose chosen profile is unchanged) / (total tasks)

so 1.0 means the updated profiles would produce exactly the same allocation and 0.0 means
every task would move. Drift signals when compatibility falls below a threshold.

Two consequences worth knowing before trusting a number from this:

  * It is a **decision-space** measure, not a parameter-space one. A large change in `rel(m)`
    that flips no decision scores 1.0 — deliberately, since re-optimising would be pointless
    — but that also means it is blind to drift that is heading somewhere bad and has not
    arrived.
  * It requires running the allocator to evaluate, so it is not cheap. §4.5's claim that
    drift detection is a lightweight signal does not obviously hold under this definition.

**077 must reconcile this against the source before any finding depends on it.**
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from poc.formulation.types import Observation, ProfileSpec

DEFAULT_ALPHA = 0.3             # EMA weight on the newest observation
DEFAULT_MIN_OBSERVATIONS = 5    # below this, suppress drift signals (§4.5)
DEFAULT_THRESHOLD = 0.9         # signal when compatibility drops below this


class NotProfiled(Exception):
    """Unprofiled entries return this, never a default value (§4.5, CLAUDE.md)."""


class ProfileStore:
    """Sole writer of profile state (§4.5). Serves immutable snapshots.

    An allocation run reads exactly one snapshot, so a bound computed during that run stays
    meaningful even if observations arrive mid-run.
    """

    def __init__(self, profiles: dict[str, ProfileSpec], alpha: float = DEFAULT_ALPHA):
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        self._profiles = dict(profiles)
        self._alpha = alpha

    def snapshot(self) -> dict[str, ProfileSpec]:
        """An immutable view. Callers may not mutate the store through it."""
        return dict(self._profiles)

    def get(self, profile_id: str) -> ProfileSpec:
        if profile_id not in self._profiles:
            raise NotProfiled(f"no profile {profile_id!r}")
        return self._profiles[profile_id]

    def record(self, observation: Observation) -> ProfileSpec:
        """Fold one observation into the profile by EMA. Returns the updated spec.

        Latency and reliability are updated; throughput, GPUs and price are properties of
        the configuration rather than of a call, so an observation cannot move them.
        """
        current = self.get(observation.profile_id)
        a = self._alpha

        updated = replace(
            current,
            latency=(1 - a) * current.latency + a * observation.latency,
            reliability=(1 - a) * current.reliability + a * (1.0 if observation.success else 0.0),
            observations=current.observations + 1,
        )
        self._profiles[observation.profile_id] = updated
        return updated


@dataclass(frozen=True)
class DriftSignal:
    compatibility: float
    threshold: float
    changed_tasks: int
    total_tasks: int
    suppressed: bool            # too few observations to be meaningful
    reason: str

    @property
    def fired(self) -> bool:
        return not self.suppressed and self.compatibility < self.threshold


class DriftDetector:
    """Signals only; never re-optimises (§4.5).

    Suppresses when observation counts are too thin to be meaningful, so a single unlucky
    call cannot trigger a re-allocation of the whole batch.
    """

    def __init__(self, allocate, threshold: float = DEFAULT_THRESHOLD,
                 min_observations: int = DEFAULT_MIN_OBSERVATIONS):
        self._allocate = allocate
        self._threshold = threshold
        self._min_observations = min_observations

    def check(self, current_routing, tasks, pools, updated_profiles, budget) -> DriftSignal:
        """Recompute the would-be decision under updated profiles and compare."""
        touched = {m for m in current_routing.values()}
        thin = [m for m in touched
                if updated_profiles[m].observations < self._min_observations]
        if thin:
            return DriftSignal(
                compatibility=1.0, threshold=self._threshold, changed_tasks=0,
                total_tasks=len(tasks), suppressed=True,
                reason=f"only {min(updated_profiles[m].observations for m in thin)} "
                       f"observations on {sorted(thin)[0]}; need {self._min_observations}")

        would_be = self._allocate(tasks, pools, updated_profiles, budget)
        if not would_be.feasible:
            return DriftSignal(
                compatibility=0.0, threshold=self._threshold,
                changed_tasks=len(tasks), total_tasks=len(tasks), suppressed=False,
                reason="no feasible allocation exists under the updated profiles")

        changed = sum(1 for t in tasks
                      if current_routing.get(t.id) != would_be.routing.get(t.id))
        compatibility = 1.0 - changed / len(tasks) if tasks else 1.0

        return DriftSignal(
            compatibility=compatibility, threshold=self._threshold,
            changed_tasks=changed, total_tasks=len(tasks), suppressed=False,
            reason=f"{changed} of {len(tasks)} tasks would move")
