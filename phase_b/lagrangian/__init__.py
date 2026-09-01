"""
Track B — Lagrangian Relaxation.

Source: de la Torre & Halappanavar (2023), JSSPP — cloud resource allocation via
demand decomposition.

Spec: docs/ARCHITECTURE.md, Section 3.2, Track B.

Three steps: constraint_relaxation.py -> decomposition.py -> multiplier_update.py
Produces a PROVEN lower bound on true optimal cost every iteration — expose it.
Owner: 075
"""
