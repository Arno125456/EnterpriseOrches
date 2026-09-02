"""
Synthetic instance generator.

Spec: docs/System_Architecture_v2.md §6.4.
Build step 3. Verified by: instances well-formed; every C(t) non-empty.
Owner: 083 (deliverable D2, due 8 Sep)

    generate(n_tasks, n_profiles, budget_tightness, seed) -> Instance

budget_tightness ∈ (0, 1] — the budget as a fraction of the GPUs needed by a naive
one-instance-per-profile solution. This is the PRIMARY EXPERIMENTAL AXIS (T3); the
comparison has no signal where the budget is loose.

The generator must guarantee C(t) is non-empty for every task, or the instance is
discarded and regenerated.
"""


def generate(n_tasks, n_profiles, budget_tightness, seed):
    raise NotImplementedError("Build step 3 — see docs/System_Architecture_v2.md §6.4")
