"""
Phase B — Multi-Workflow Optimizer. PRIMARY ACTIVE FOCUS.

Spec: docs/ARCHITECTURE.md, Section 3.

Two tracks, both reading the same shared ledger and profiled data, built for direct
comparison:
    phase_b/heft/         Track A — fast, one-pass, no optimality-gap guarantee
    phase_b/lagrangian/   Track B — iterative, produces a proven optimality-gap bound

Both reuse the same inner decision rule (feasibility filter + argmin-cost) as their
per-task / per-workflow solver — see inner_rule.py.
"""
