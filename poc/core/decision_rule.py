"""
select_profile — the one inner rule all three tracks call (principle P4).

Spec: docs/System_Architecture_v2.md §5.2.1.
Build step 6. Verified by: known pools with hand-computed picks; all-infeasible returns None.
Owner: 075

`cost_adjust` is the seam that lets the tracks share this rule:

    Track A       admit.extra_cost                    marginal provisioning cost only
    Track B       admit.extra_cost + λ[task]          plus the relaxed assignment multiplier
    Track C       admit.extra_cost                    (repair pass)

Complexity: O(|C(t)|) per task. The pool passed in is C(t), already floor-filtered —
floors are applied by construction, never weighted against cost (principle P3).
"""


def select_profile(task, pool, state, cost_adjust):
    """Return the winning profile id, or None if no profile is admissible within budget.

    None means Infeasible(reason="no profile admissible within budget",
                          blockingTask=task.id, constraint="C3").
    """
    raise NotImplementedError("Build step 6 — see docs/System_Architecture_v2.md §5.2.1")
