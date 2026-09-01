"""
Executor Registry — manual registration, Murakkab's 3-field schema
(description, interface spec, configurable knobs).

Spec: docs/ARCHITECTURE.md, Section 2.3.

No auto-discovery. A developer registers each executor by hand under a task_type.
Layer 1 (phase_a/) does an exact-match lookup against this registry.

Owner: 083 (infra), 035 (Layer 1 consumer)
"""
