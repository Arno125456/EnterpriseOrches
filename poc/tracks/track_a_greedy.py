"""
Track A — plain greedy construction.

Spec: docs/System_Architecture_v2.md §5.2.2.
Build step 9. Verified by: satisfies I1-I5; returns 300 on adversarial_3t2p.
Owner: 035

PLAIN GREEDY ONLY. No relocate, no consolidate, no elaborate multi-start — T4 decides
whether any of that is worth building (v2 §6.5, PoC plan §5.1).

Known weakness, by construction: cost_to_admit is myopic. It prices a task against the
*current* provisioning state, so early tasks may open instances that later tasks would have
made unnecessary, or vice versa.

The fixture in instances/fixtures/adversarial_3t2p.py is a verified instance of exactly
that failure — and it goes further. By exhaustive enumeration, all six orderings return 300,
and no single-move relocate recovers 280 either, because the improving move is t1 and t2
*together*. So Track A needs a multi-move neighbourhood or a consolidation step; multi-start
plus single-move relocate is provably insufficient there. That is a T2/T4 finding already in
hand — do not re-derive it, and do not let it become an argument for building relocate
before T4 says so.

Complexity: O(|orderings| · |T| · max|C(t)|).
"""


def allocate(tasks, pools, profiles, budget, seed=0):
    raise NotImplementedError("Build step 9 — see docs/System_Architecture_v2.md §5.2.2")
