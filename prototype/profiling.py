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

DEFAULT_ALPHA = 0.3             # EMA weight on the newest observation (latency only)
# Decay sets the effective sample size at 1/(1 - decay). That ceiling matters more than it
# looks: with a prior of p, an unbroken run of successes converges to (N + p) / (N + 2p), so
# a short memory imposes a CEILING on achievable reliability. At decay 0.98 (N = 50) and a
# Laplace prior of 1.0 that ceiling is 51/52 = 0.981 — and any task with rel_floor 0.99
# would have been permanently unservable by a measured profile. At decay 0.995 (N = 200)
# with a Jeffreys prior of 0.5 the ceiling is 0.9975, which clears realistic floors.
DEFAULT_DECAY = 0.995           # effective sample size ~200
DEFAULT_PRIOR = 0.5             # Jeffreys prior
DEFAULT_MIN_OBSERVATIONS = 5    # below this, suppress drift signals (§4.5)
DEFAULT_THRESHOLD = 0.9         # signal when compatibility drops below this


class NotProfiled(Exception):
    """Unprofiled entries return this, never a default value (§4.5, CLAUDE.md)."""


class ProfileStore:
    """Sole writer of profile state (§4.5). Serves immutable snapshots.

    An allocation run reads exactly one snapshot, so a bound computed during that run stays
    meaningful even if observations arrive mid-run.
    """

    def __init__(self, profiles: dict[str, ProfileSpec], alpha: float = DEFAULT_ALPHA,
                 decay: float = DEFAULT_DECAY, prior: float = DEFAULT_PRIOR):
        if not 0.0 < alpha <= 1.0:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        if not 0.0 < decay <= 1.0:
            raise ValueError(f"decay must be in (0, 1], got {decay}")
        self._profiles = dict(profiles)
        self._alpha = alpha
        self._decay = decay
        self._prior = prior
        # Seeded from the declared reliability so a profile does not start from the prior
        # and immediately look unreliable. Weighted as a few effective observations.
        self._counters = {
            pid: (spec.reliability * 5.0, 5.0) for pid, spec in profiles.items()
        }

    def snapshot(self) -> dict[str, ProfileSpec]:
        """An immutable view. Callers may not mutate the store through it."""
        return dict(self._profiles)

    def get(self, profile_id: str) -> ProfileSpec:
        if profile_id not in self._profiles:
            raise NotProfiled(f"no profile {profile_id!r}")
        return self._profiles[profile_id]

    def record(self, observation: Observation) -> ProfileSpec:
        """Fold one observation into the profile. Returns the updated spec.

        Throughput, GPUs and price are properties of the configuration rather than of a
        call, so an observation cannot move them.

        LATENCY uses the EMA that §4.5 specifies. It is a continuous quantity and an EMA
        tracks drift in it correctly.

        RELIABILITY DOES NOT, AND §4.5 IS WRONG ABOUT THIS. Applying an EMA to a binary
        success/failure signal is catastrophically volatile: with alpha 0.3, a profile at
        0.99 that sees 99 successes and then one failure reports **0.70**. One failed call
        makes it ineligible for any task with a floor above 0.7, for roughly eight
        subsequent successes. The reliability floor — the entire mechanism behind the
        project's reliability pillar — would be driven by single-call noise.

        Instead reliability is a **decayed counting estimator** with a Laplace prior:

            rel = (decayed successes + prior) / (decayed trials + 2 * prior)

        Both counters decay by DECAY per observation, so recent behaviour still dominates
        and genuine degradation is still detected — the property the EMA was chosen for —
        but a single failure moves the estimate by roughly one effective sample instead of
        by 30% of the way to zero. Under the same 99-successes-then-a-failure sequence this
        reports about 0.97.

        `observations` counts raw observations, so the drift detector's suppression rule is
        unaffected.
        """
        current = self.get(observation.profile_id)
        a = self._alpha
        pid = observation.profile_id

        successes, trials = self._counters.get(pid, (0.0, 0.0))
        successes = successes * self._decay + (1.0 if observation.success else 0.0)
        trials = trials * self._decay + 1.0
        self._counters[pid] = (successes, trials)

        updated = replace(
            current,
            latency=(1 - a) * current.latency + a * observation.latency,
            reliability=(successes + self._prior) / (trials + 2 * self._prior),
            observations=current.observations + 1,
        )
        self._profiles[pid] = updated
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
