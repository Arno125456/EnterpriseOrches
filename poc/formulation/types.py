"""
Data model — Task, ProfileSpec, AllocationResult, Infeasible, Observation.

Spec: docs/System_Architecture_v2.md §5.1.
Build step 1. Verified by: types instantiate; no logic to test.
Owner: 083

Fields are specified in full in §5.1. Reproduced here as the contract, not restated
in prose:

    TaskId          workflowId, taskName
    Task            id, taskType, load, relFloor, latCeil, successors
                    (successors are execution ordering only — not in the optimisation)
    ProfileSpec     id, declaredType, throughput, gpus, price, reliability, latency,
                    observations
    Instance        profileId, count                        # n[m]
    AllocationResult routing (x), provisioning (n), totalCost, gpusUsed, lowerBound,
                    strategy, iterations, restarts, converged, computeTime, feasible
    Infeasible      reason, blockingTask, constraint in {"C1","C2","C3"}
    Observation     taskId, profileId, latency, success, cost, timestamp

BLOCKED ON O1 — does the objective include a per-invocation term
`Σ x[t][m]·varcost(t,m)`? It changes the objective signature everywhere, so it is a
human decision before this file is written. Default assumption: no, provisioning cost
only. See CLAUDE.md "Open questions".
"""

# Build step 1 — not yet written. Blocked on O1 (see docstring above).
