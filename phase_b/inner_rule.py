"""
The reusable inner decision rule — feasibility filter, then argmin-cost among survivors.

Spec: docs/ARCHITECTURE.md, Section 3.3.

This is called by BOTH Track A (HEFT's assignment step) and Track B (Lagrangian's
per-workflow subproblem solver). Build this first — both tracks depend on it.

Owner: 075
"""

def select_candidate(task, eligible_candidates, floors, remaining_shared_capacity, profile_store):
    """
    minimize      cost(c)
    subject to    reliability(c)  >= R_min(t)
                  latency(c)      <= L_min(t)
                  consumption(c)  <= remaining_shared_capacity
    over          c in eligible_candidates(t)

    Returns the winning candidate, or None if infeasible.
    """
    raise NotImplementedError("T14a/T14b — see docs/ARCHITECTURE.md Section 3.3")
