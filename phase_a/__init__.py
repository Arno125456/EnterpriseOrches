"""
Phase A — Workflow Ingestion & Layer 1 Eligibility Lookup

Spec: docs/ARCHITECTURE.md, Section 2.

Job: take a batch of incoming DAGs (offline — fixed before Phase B runs) and, for every
task, determine which registered executors are eligible. Does NOT pick a winner — that's
Phase B's job (registry/ + phase_b/).

Owner: 035
"""
