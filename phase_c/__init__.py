"""
Phase C — Execution + Continuous Profiling.

Spec: docs/ARCHITECTURE.md, Section 4.

Three distinct profiled things (Section 4.4):
    1. Task-Candidate Profile   — cost/latency/reliability per (task_type, candidate)
    2. Workflow Arrival/Demand  — NOT YET BUILT, conditional, only if a future
                                   capacity-split policy needs it
    3. Compatibility/Drift Score — computed from #1, fires Phase B re-runs (only Phase B)

Owner: 077
"""
