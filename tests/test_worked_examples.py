"""
Regression tests — must reproduce the worked examples in docs/ARCHITECTURE.md exactly.

Per Task_Management.xlsx T25b: "CI fails loudly if any algorithm drifts from
documented examples." This file is the seed for that — currently all skipped until
phase_b/inner_rule.py (T14a/T14b) is implemented.
"""
import pytest


@pytest.mark.skip(reason="T14a/T14b not yet implemented — see phase_b/inner_rule.py")
def test_inner_rule_matches_original_worked_example():
    """
    docs/ARCHITECTURE.md Section 3.3's worked example (originally from the
    single-workflow design): given the standard candidate table (fast-parser,
    small-model, lookup-tool, template-fill), the inner rule should reproduce a
    total cost of $0.017 — the same result documented in the architecture doc.
    """
    from phase_b.inner_rule import select_candidate  # noqa: F401
    raise NotImplementedError


@pytest.mark.skip(reason="phase_b/heft not yet implemented")
def test_heft_multiworkflow_no_double_booking():
    """
    Given the 3-workflow real-data batch (data/eval_batches/eval_batch_3workflows.json),
    HEFT's assignment walk must never allocate more than the shared pool's total
    capacity across all 3 concurrent workflows combined.
    """
    raise NotImplementedError


@pytest.mark.skip(reason="phase_b/lagrangian not yet implemented")
def test_lagrangian_produces_valid_lower_bound():
    """
    Lagrangian relaxation's reported lower bound must never exceed the true
    MILP-optimal cost for the same batch (scripts/offline_baselines/milp_baseline.py
    extended to multi-workflow scope — see T27b).
    """
    raise NotImplementedError
