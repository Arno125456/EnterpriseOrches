"""
Cost, runtime, bound, gap, feasibility.

Spec: docs/System_Architecture_v2.md §6.1.
Build step 10. Owner: 089

The gap that matters for T4 is cost-to-optimum, which needs the exact MILP result — so
these are only meaningful on instances small enough to solve exactly. That is deliberate;
the PoC establishes no performance claims at scale (PoC plan §5.7).
"""


def gap_to_optimum(result, optimum_cost):
    raise NotImplementedError("Build step 10")


def summarise(results):
    raise NotImplementedError("Build step 10")
