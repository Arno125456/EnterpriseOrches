"""
Profile Store and Drift Detector (§4.5). Outside PoC scope. Owner: 077.
"""
from datetime import datetime

import pytest

from poc.formulation.types import Observation, ProfileSpec, Task, TaskId
from poc.tracks import exact_milp
from prototype.profiling import DriftDetector, NotProfiled, ProfileStore


def spec(pid, rel=0.95, lat=50.0, obs=0):
    return ProfileSpec(pid, "generic", throughput=20.0, gpus=1, price=100.0,
                       reliability=rel, latency=lat, observations=obs)


def observation(pid, latency=50.0, success=True):
    return Observation(TaskId("wf", "t1"), pid, latency, success, 0.0, datetime.now())


def test_ema_moves_toward_the_observation():
    store = ProfileStore({"m": spec("m", lat=50.0)}, alpha=0.5)
    updated = store.record(observation("m", latency=100.0))
    assert updated.latency == pytest.approx(75.0)
    assert updated.observations == 1


def test_failure_pulls_reliability_down():
    store = ProfileStore({"m": spec("m", rel=1.0)}, alpha=0.5)
    assert store.record(observation("m", success=False)).reliability == pytest.approx(0.5)


def test_unprofiled_raises_rather_than_defaulting():
    """Unprofiled entries return NotProfiled, never a default (CLAUDE.md conventions)."""
    with pytest.raises(NotProfiled):
        ProfileStore({}).get("missing")


def test_snapshot_does_not_alias_the_store():
    """An allocation run reads exactly one snapshot, so a bound stays meaningful (§4.5)."""
    store = ProfileStore({"m": spec("m", lat=50.0)})
    snap = store.snapshot()
    store.record(observation("m", latency=500.0))
    assert snap["m"].latency == 50.0


def _instance():
    tasks = [Task(TaskId("wf", f"t{i}"), "generic", load=8.0, rel_floor=0.0, lat_ceil=1e9)
             for i in range(3)]
    profiles = {"cheap": spec("cheap", obs=99), "dear": spec("dear", obs=99)}
    profiles["dear"] = ProfileSpec("dear", "generic", 20.0, 1, 300.0, 0.99, 50.0, 99)
    pools = {t.id: ["cheap", "dear"] for t in tasks}
    return tasks, pools, profiles


def test_drift_is_suppressed_when_observations_are_thin():
    """A single unlucky call must not re-allocate the batch (§4.5)."""
    tasks, pools, profiles = _instance()
    profiles = {k: ProfileSpec(**{**v.__dict__, "observations": 1}) for k, v in profiles.items()}
    detector = DriftDetector(exact_milp.allocate, min_observations=5)
    signal = detector.check({t.id: "cheap" for t in tasks}, tasks, pools, profiles, 4)
    assert signal.suppressed and not signal.fired


def test_no_drift_when_the_decision_is_unchanged():
    tasks, pools, profiles = _instance()
    detector = DriftDetector(exact_milp.allocate)
    routing = exact_milp.allocate(tasks, pools, profiles, 4).routing
    signal = detector.check(routing, tasks, pools, profiles, 4)
    assert signal.compatibility == pytest.approx(1.0)
    assert not signal.fired


def test_drift_fires_when_the_decision_would_change():
    """The score is a decision-space measure: it moves only when routing would move."""
    tasks, pools, profiles = _instance()
    detector = DriftDetector(exact_milp.allocate)
    stale = {t.id: "dear" for t in tasks}          # pretend we had chosen the dear profile
    signal = detector.check(stale, tasks, pools, profiles, 4)
    assert signal.compatibility < 1.0 and signal.fired


def test_score_is_blind_to_parameter_change_that_flips_no_decision():
    """A documented weakness of the [PROPOSED] definition, asserted so it is not forgotten."""
    tasks, pools, profiles = _instance()
    detector = DriftDetector(exact_milp.allocate)
    routing = exact_milp.allocate(tasks, pools, profiles, 4).routing

    nudged = dict(profiles)
    nudged["dear"] = ProfileSpec("dear", "generic", 20.0, 1, 290.0, 0.99, 50.0, 99)
    signal = detector.check(routing, tasks, pools, nudged, 4)
    assert signal.compatibility == pytest.approx(1.0), "price moved, no decision changed"
