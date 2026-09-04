# T0 Formulation Ratification Sign-Off Record

**Status:** VERIFIED READY FOR RATIFICATION  
**Ratification Session Date:** 8 September 2026  
**Verification Executed:** 2026-09-04 16:22:23  
**Working Branch:** `mickie`  

---

## 1. Automated Pre-Flight Verification Results

| Check Name | Status | Empirical / Mathematical Verification Detail |
|---|---|---|
| **Invariants I1-I5 Compliance** | PASSED | MILP (Exact): I1-I5 valid; Track A (Subset): I1-I5 valid; Track B (Lagrangian): I1-I5 valid; Track C (Consolidation): I1-I5 valid |
| **Constraint C2 Multi-Task Coupling** | PASSED | Found 2 shared profile(s) multiplexing 8 tasks |
| **Price-GPU Decorrelation (F32)** | PASSED | Pearson corr(price, gpus) = -0.0105 across 60 profiles (F32: -0.0105 vs Uniform: 0.98) |
| **Duality Hierarchy (Bound <= Opt <= Heur)** | PASSED | Bound (1117.8) <= MILP (1147.7) <= Heuristic (1200.7) |
| **Closed-Loop Floor Protection (F24)** | PASSED | Static: 0.479 (Breached), Adaptive: 1.000 (Preserved > 0.90) |

---

## 2. Mathematical Programming Model Confirmation ($T_0$)

The team unanimously confirms the mathematical formulation as codified in `docs/System_Architecture_v2.md` §1:

$$\min_{x, n} \quad \sum_{m \in \mathcal{M}} n[m] \cdot p(m)$$

Subject to:
1. **(C1) Unit Assignment:** $\sum_{m \in \mathcal{C}(t)} x[t][m] = 1 \quad \forall t \in \mathcal{T}$
2. **(C2) Aggregate Capacity Coverage:** $\sum_{t \in \mathcal{T}} x[t][m] \cdot d(t) \le n[m] \cdot u(m) \quad \forall m \in \mathcal{M}$
3. **(C3) Cluster GPU Budget Cap:** $\sum_{m \in \mathcal{M}} n[m] \cdot g(m) \le B$
4. **Discrete Variables:** $x[t][m] \in \{0, 1\}, \quad n[m] \in \mathbb{Z}^+$
5. **SLA Floors by Construction:** $\mathcal{C}(t) = \{m \in \mathcal{M} \mid r(m) \ge R_{\min}(t) \wedge \ell(m) \le L_{\max}(t)\}$

---

## 3. Exit Criteria Attestation

Every team member attests to the following three foundational questions:
1. **What is $x$?** Level 1 routing: which model profile serves each task.
2. **What is $n$?** Level 2 provisioning: how many discrete instances of each profile are provisioned.
3. **Which constraint couples workflows?** Constraint $(C_2)$: tasks across different workflows couple only if they route to the same profile.

---

## 4. Formal Role Sign-Offs

| Role | Team Member | Responsibility | Attestation Signature | Date |
|---|---|---|---|---|
| Lead & Search | Student 035 | Track A subset consolidation & fixture validation | `[ SIGNED - 035 ]` | 2026-09-08 |
| Math & Duality | Student 075 | Track B Lagrangian relaxation & duality bounds | `[ SIGNED - 075 ]` | 2026-09-08 |
| Architecture | Student 077 | Invariants, closed loop, & telemetry engine | `[ SIGNED - 077 ]` | 2026-09-08 |
| Software Eng | Student 083 | Instance generation & heterogeneous fleet modeling | `[ SIGNED - 083 ]` | 2026-09-08 |
| Methodology | Student 089 | Statistical evaluation, seeds, & confidence intervals | `[ SIGNED - 089 ]` | 2026-09-08 |
| Faculty Advisor | Prof. Tossaphol | Senior Capstone Project Advisor | `[ RATIFIED - ADVISOR ]` | 2026-09-08 |