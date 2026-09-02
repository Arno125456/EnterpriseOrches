"""
Run all conditions under matched inputs.

Spec: docs/System_Architecture_v2.md §4.7.
Build step 10. Owner: 089

Matched conditions are not a detail. Any condition this project introduces that Murakkab's
evaluation did not use requires the MILP baseline to be re-run under it before an
improvement is claimed (v2 §4.7).

Determinism: every track takes seed; randomised orderings derive from it, so runs
reproduce exactly (principle P10).
"""


def run_conditions(instance, strategies, seed=0):
    raise NotImplementedError("Build step 10 — see docs/System_Architecture_v2.md §4.7")
