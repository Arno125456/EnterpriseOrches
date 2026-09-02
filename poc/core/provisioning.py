"""
ProvisioningState — instances per profile, load per profile, GPUs consumed.

Spec: docs/System_Architecture_v2.md §4.4, §6.3.
Build step 5. Verified by: admit/release/snapshot/restore sequences; budget rejection.
Owner: 083

This component is the correction at the heart of v2. v1 modelled a slot pool decremented
per task. Under (C2)-(C3) a task consumes no resource directly — it adds *load*, which may
or may not force a new instance.

`cost_to_admit` is the most important operation in the system. It answers "what does routing
this task here cost right now" — and its answer changes as other tasks are admitted. That
state-dependence IS the aggregate-coupling problem, made explicit rather than hidden. Get it
right first; T2 and T4 both turn on it.

    AdmitCost { extra_instances, extra_gpus, extra_cost }
    extra_instances == 0 when existing headroom covers the task.

`snapshot`/`restore` exist for Track A's multi-start and Track C's rounding repair.
"""


class ProvisioningState:
    def __init__(self, profiles, budget):
        raise NotImplementedError("Build step 5 — see docs/System_Architecture_v2.md §4.4")

    def cost_to_admit(self, task, profile_id):
        """AdmitCost, or None if extra_gpus would exceed remaining budget."""
        raise NotImplementedError("Build step 5")

    def admit(self, task, profile_id):
        raise NotImplementedError("Build step 5")

    def release(self, task, profile_id):
        raise NotImplementedError("Build step 5")

    def snapshot(self):
        raise NotImplementedError("Build step 5")

    def restore(self, snap):
        raise NotImplementedError("Build step 5")

    def build_provisioning(self):
        """dict[profile_id, int] — n[m]."""
        raise NotImplementedError("Build step 5")

    def total_cost(self):
        raise NotImplementedError("Build step 5")

    def gpus_used(self):
        raise NotImplementedError("Build step 5")
