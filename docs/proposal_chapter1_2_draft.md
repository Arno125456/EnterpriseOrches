# Chapter 1: Introduction, Problem Formulation, and Objectives

**Senior Capstone Design Proposal**  
**Working Title:** Profile-Guided Multi-Workflow Resource Orchestration Platform  
**Authors:** Student IDs 035, 075, 077, 083, 089  
**Faculty Advisor:** Prof. Tossaphol  
**Date:** September 2026  

---

## 1.1 Context and Motivation: The Enterprise LLM Resource Dilemma

Enterprise software systems are undergoing a rapid architectural transition: monolithic single-prompt Large Language Model (LLM) queries are being replaced by **multi-stage agentic workflows** structured as Directed Acyclic Graphs (DAGs). These pipelines—spanning document extraction, multi-agent debate, code synthesis, iterative verification, and Retrieval-Augmented Generation (RAG)—require executing sequences of heterogeneous specialized tasks.

In enterprise private clouds and managed compute clusters, hardware resources—specifically High-Bandwidth Memory (HBM) accelerators such as NVIDIA A100 and H100 GPUs—are scarce, expensive, and subject to strict aggregate budgetary caps. When multiple enterprise departments submit concurrent workflow DAGs against a shared cluster, an orchestrator must make two fundamentally coupled decisions:
1. **Level 1 (Logical Routing):** Which serving profile (model architecture, quantization level, and execution backend) should be assigned to execute each logical workflow task?
2. **Level 2 (Physical Provisioning):** Exactly how many discrete physical server instances of each serving profile should be provisioned to satisfy aggregate throughput demand without exceeding the cluster's GPU budget?

Today, enterprise workflow frameworks (e.g., LangGraph, AutoGen, CrewAI) treat these decisions as disconnected, ad-hoc choices. Individual application developers select model endpoints statically, typically choosing oversized flagship models (e.g., 70B parameters on 4×A100 instances) to guarantee output quality. When deployed across a multi-tenant cluster, uncoordinated provisioning results in catastrophic resource fragmentation: instances sit 60–80% under-utilized, GPU quotas are exhausted prematurely, and concurrent critical tasks are stranded.

---

## 1.2 Problem Statement: Why Static Allocation Fails Under Drift

State-of-the-art cloud orchestration platforms, such as *Murakkab* (Chaudhry et al., *OSDI '26*), formulate joint model selection and hardware provisioning as an offline Mixed-Integer Linear Program (MILP). While this achieves significant static cost savings over uncoordinated baselines, it relies on a foundational assumption that breaks in production: **that profile performance parameters (latency, throughput, and reliability) are static, declared constants.**

In real-world serving environments, empirical parameters **drift continuously**:
1. **Non-Stationary Reliability:** Upstream prompt variability, non-deterministic token lengths, context-window overflow, and backend connection timeouts cause empirical task success rates to deviate significantly from vendor benchmarks.
2. **Dynamic Latency Fluctuations:** Multi-tenant memory bus contention, noisy neighbors, and KV-cache thrashing introduce unpredictable latency spikes.
3. **The Static Allocation Breakdown:** Under empirical drift, a static allocator that solves the provisioning problem once at admission operates open-loop. As proven in our empirical findings (Finding **F24**), **a static allocator silently breaches enterprise SLA floors (delivering an empirical reliability of 0.542 against a declared 0.95 floor), completely blind to ongoing failure.**

```
+-------------------------------------------------------------------------------+
|                      THE OPEN-LOOP ORCHESTRATION BREAKDOWN                    |
+-------------------------------------------------------------------------------+
| 1. Admission:    Tasks routed to Profile A based on declared 99% reliability. |
| 2. Execution:    Inference load causes memory pressure; empirical rel -> 50%. |
| 3. Static State: Allocator remains unaware; continues routing critical tasks. |
| 4. SLA Outcome:  Catastrophic silent failure (0.542 delivered vs. 0.95 floor).|
+-------------------------------------------------------------------------------+
```

Simply re-solving the allocation via an exact solver upon every telemetry event is computationally intractable. Exact mixed-integer solvers scale poorly: at 128 tasks, exact MILP exhibits heavy-tailed runtimes averaging **12.3 ± 10.3 seconds**, with adversarial instances running for minutes or hanging without timeouts (Finding **F13**, **F29**). A high-frequency telemetry loop cannot tolerate an optimizer that periodically stalls.

---

## 1.3 Project Objectives and Research Questions

To resolve this dilemma, this project designs, implements, and evaluates the **Profile-Guided Multi-Workflow Resource Orchestration Platform (CapOrches)**. The platform operates as a robust closed loop: continuously measuring empirical execution telemetry, maintaining Bayesian profile estimates, detecting decision-relevant drift, and triggering global re-allocation via a fast, predictable solving engine.

### Research Questions ($T_0–T_4$)
* **$T_0$ (Mathematical Formulation):** Can joint task routing and instance provisioning under hard GPU budgets and SLA floors be formulated as a rigorous, solvable mathematical program?
* **$T_1$ (Lagrangian Duality & Optimality Certificates):** Does Lagrangian relaxation of unit assignment ($C_1$) or budget ($C_3$) produce tractable, high-quality dual lower bounds to certify solution quality?
* **$T_2$ (Heuristic Foundations):** Can constructive greedy heuristics find near-optimal allocations, or does aggregate capacity coupling across shared instances create structural failure modes?
* **$T_3$ (Budget Operating Regimes):** How does the cluster GPU budget cap constrain the feasible operating region, and where do heuristic phase transitions occur?
* **$T_4$ (Regime-Dependent Solving):** Under what scale and tightness conditions is heuristic solving justified over exact MILP or continuous LP relaxation?

---

## 1.4 Core Contributions

The primary contributions of this capstone research project are:
1. **The Closed-Loop Orchestration Paradigm:** We establish an adaptive feedback architecture that measures empirical execution telemetry, updates profile parameters using a decayed counting estimator with Jeffreys prior, and triggers re-optimization when decision-space compatibility drops below threshold.
2. **Empirical Verification of Floor Protection (Finding F24):** We demonstrate on matched-seed drift simulations that while static allocators suffer catastrophic SLA violations (0.542 delivered vs. 0.95 floor), our closed loop actively detects drift and preserves SLA floors (**0.938 delivered, yielding a paired benefit of +0.424 [0.405, 0.442]**, $n=20$).
3. **Upper Confidence Bound (UCB) Filtering (Finding F25):** We prove that filtering candidate profiles on point estimates causes a permanent 40% cost overpayment due to transient noise. We design a UCB filtering mechanism that recovers the global optimum with zero variance.
4. **Predictable Sub-Second Solving (`C+cons`):** We design a continuous LP relaxation pipeline coupled with a multi-move capacity consolidation repair pass (`C+cons`). At 128 tasks, `C+cons` delivers bounded, predictable execution in **0.106 ± 0.020 seconds** with an optimality gap of **3.03 ± 1.62%**, eliminating solver heavy tails.
5. **Heterogeneous Fleet Trade-Off Validation (Finding F31 & F32):** We implement a heterogeneous fleet generator reflecting empirical cloud pricing tiers (Commodity T4, Standard A100, Premium H100), proving that price is decorrelated from GPU count ($\text{corr} = -0.0105$) and that the GPU budget $(C_3)$ actively trades off physical hardware against financial cost.
6. **Production-Grade Implementation & Verification:** A complete, warning-free codebase with **646 automated tests (642 passing, 4 skipped)** validating mathematical invariants, algorithmic correctness, and closed-loop behavior.

---

# Chapter 2: Literature Review and Theoretical Positioning

---

## 2.1 Scope of the Literature Review

Our theoretical framework synthesizes twelve foundational research papers categorized across three core scopes:
* **Scope $S_1$ (Workflow Orchestration & Declarative DAGs):** Systems decoupling logical pipeline specifications from physical execution environments.
* **Scope $S_2$ (Resource Allocation, Routing, & Optimization):** Algorithmic mechanisms for task-to-model-to-hardware assignment under capacity constraints.
* **Scope $S_3$ (Empirical Methodology & Evaluation):** Experimental design, drift detection, and statistical validation in non-stationary ML serving.

---

## 2.2 Workflow Orchestration Systems ($S_1$)

### 2.2.1 Declarative Pipelines and Logical-Physical Decoupling
Traditional agentic frameworks—including LangChain, AutoGen (*Wu et al., 2023*), and CrewAI—tightly couple prompt engineering with physical model endpoints. Developers hard-code specific model identifiers (e.g., `gpt-4o` or `claude-3-5-sonnet`) directly into individual agent functions.

*DSPy* (*Khattab et al., ICLR 2024, Paper P12*) introduced the foundational principle of **separating declarative pipeline structure from execution parameter optimization**. In DSPy, workflows are expressed as typed modular programs; an automated compiler optimizes prompt instructions and demonstration few-shot examples against formal metric evaluators. 

Our architecture extends this separation of concerns to **systems-level infrastructure**:
* Application developers specify **logical workflow DAGs** with declarative task requirements (throughput demand, latency ceilings $L_{\max}$, and reliability floors $R_{\min}$).
* The platform's allocation engine independently determines the **physical realization**: mapping logical tasks to concrete serving profiles and provisioning GPU worker pools.

---

## 2.3 Resource Allocation and Serving Optimization ($S_2$)

### 2.3.1 Mixed-Integer Linear Programming in Cloud Serving: Murakkab
*Murakkab* (*Chaudhry et al., OSDI '26, Paper P1*) established the benchmark for multi-tenant agentic workflow orchestration in cloud platforms. Murakkab addresses combinatorial configuration spaces by mapping workflows to a logical DAG, profiling models ahead of time, and solving a centralized Mixed-Integer Linear Program (MILP) using Gurobi with a 300-second time limit.

Murakkab demonstrated that cross-workflow instance colocation and multiplexing reduces GPU usage by up to 2.8× and dollar costs by up to 4.3×. However, Murakkab operates on a coarse, periodic optimization epoch (e.g., 60 minutes) and assumes profile parameters are static inputs. Our work differs fundamentally:
1. **Cadence and Responsiveness:** Rather than waiting for a 60-minute batch window, our system continuously monitors execution telemetry and triggers immediate re-allocation upon detecting decision-relevant drift.
2. **Computational Tractability:** Rather than relying on commercial exact solvers with multi-minute timeouts, we provide polynomial-time heuristics (`C+cons`) delivering bounded runtimes under 100 milliseconds.

### 2.3.2 Constructive Heuristics & Activation Ranking: Cheng & Nguyen
*Cheng & Nguyen* (*arXiv:2604.07472, 2026, Paper P3*) proposed constructive heuristic frameworks for multi-workflow allocation, introducing greedy activation-cost ranking and lookahead feasibility filtering (`C_FEASFIRST`).

In our research, we evaluated whether constructive greedy methods can serve as the primary allocator. In Finding **F8**, we proved that plain greedy heuristics are structurally defeated on adversarial instances due to **aggregate capacity coupling**: when multiple tasks share a single provisioned instance, sequential greedy placement cannot see the joint cost reduction of moving multiple tasks simultaneously. We resolved this fundamental limitation by designing the **subset consolidation neighborhood (`A+subset`)**, which evaluates simultaneous relocations of task subsets ($k \le 2$), achieving global optimality on coupled fixtures.

---

## 2.4 Drift, Uncertainty, and Opacity in Machine Learning Systems

### 2.4.1 Update Opacity and Update Compatibility: Hatherley & Bansal et al.
A critical theoretical challenge in adaptive systems is understanding the operational impact of continuous updates. *Hatherley* (*2025, Ethics and Information Technology, Paper P9*) investigated **update opacity**—the inability of users to predict or explain why an updated ML model produces a different decision than its predecessor on functionally identical inputs. This causes *intra-ML disagreement* (diachronic evolution over time), disrupting learned trust and operational workflows.

Hatherley evaluated mitigation strategies, formalizing the concept of **Update Compatibility** following *Bansal et al.* (*2019, Updates in AI*). Update compatibility measures the fraction of decisions preserved across an update:
$$C(h_2, h_1) = \frac{|\{x \in \mathcal{D} \mid h_2(x) = h_1(x)\}|}{|\mathcal{D}|}$$

We operationalize this literature concept in our **Drift Detection Engine** ([`prototype/profiling.py`](file:///D:/intern/EnterpriseOrches/prototype/profiling.py)):
$$\text{Compatibility}(A_{\text{new}}, A_{\text{old}}) = \frac{|\{t \in \mathcal{T} \mid A_{\text{new}}(t) = A_{\text{old}}(t)\}|}{|\mathcal{T}|}$$
Rather than triggering re-optimization on raw parameter shifts that would not alter physical routing, our engine evaluates compatibility in the **discrete decision space**. Re-allocation is triggered only when compatibility drops below a tuned threshold (e.g., $\tau = 0.90$), preventing unnecessary cluster churn and minimizing update opacity.

---

## 2.5 Theoretical Foundation: Modular Capacitated Facility Location (MCFLP-B)

The offline allocation problem belongs to the class of **Modular Capacitated Facility Location Problems with Budget Constraints (MCFLP-B)** (*Geoffrion, 1974; Fisher, 1981*). 

In our formulation:
* Model serving profiles $m \in \mathcal{M}$ correspond to candidate facilities with modular capacity steps $u(m)$ and opening costs $p(m)$.
* Logical tasks $t \in \mathcal{T}$ correspond to customer demands $d(t)$ that must be assigned to open facilities.
* The cluster GPU limit $B$ acts as a global knapsack side-constraint.

### Lagrangian Relaxation Duality Hierarchy
To evaluate theoretical bounds ($T_1$), we investigated two alternative Lagrangian relaxations:
1. **$(C_1)$ Assignment Relaxation (Track B):** Dualizing $\sum_m x[t][m] = 1$ with multipliers $\lambda_t \in \mathbb{R}$ decomposes the problem into independent integer knapsack subproblems per profile. Because each profile retains discrete instance steps $n[m] \in \mathbb{Z}^+$, it preserves the non-convex step-function that continuous LP relaxes. As proven in Finding **F30**, Track B's Lagrangian dual bound is strictly tighter on 100% of tested instances, sitting a paired **12.57 percentage points [9.49, 15.64]** closer to the true integer optimum than the LP bound.
2. **$(C_3)$ Budget Relaxation (Track B-C3):** Dualizing $\sum_m n[m] g(m) \le B$ with scalar multiplier $\mu \ge 0$ yields a 1D concave dual curve solved via bisection in **<1 ms**. The resulting optimal dual bound matches the continuous LP bound to five decimal places ($|Z_{\text{dual}} - Z_{\text{LP}}| \le 2\times 10^{-5}$), confirming linear programming duality under discrete instance recovery (Finding **F21**).

---

## 2.6 The Novelty Boundary Matrix (Advisor Question O12)

We formally delineate the scientific novelty boundary of this research:

| Dimension | Murakkab (*Chaudhry et al., 2026*) | Cheng & Nguyen (*2026*) | **This Project (CapOrches)** |
|---|---|---|---|
| **Problem Formulation** | Static MILP (Facility Location) | Greedy Activation Ranking | **MCFLP-B with SLA Floors ($R_{\min}, L_{\max}$)** |
| **Profile Parameters** | Static benchmarks / Declared | Declared constants | **Empirically Measured & Bayesian Updated** |
| **Reliability Tracking** | None | None | **Decayed Counting with Jeffreys Prior (F19)** |
| **Filtering Mechanism** | Point-estimate feasibility | Point-estimate feasibility | **Upper Confidence Bound (UCB) Filtering (F25)** |
| **Drift Detection** | Coarse 60-min periodic epoch | None (open-loop) | **Decision Compatibility $C(A_{\text{new}}, A_{\text{old}})$ (P9)** |
| **Re-Optimization** | Static offline solve | Single-pass | **Continuous Global Re-Allocation** |
| **Solver Runtime** | 300s time limit (Gurobi) | Fast heuristic | **Predictable 0.106s Bounded LP Repair (`C+cons`)** |

**Summary of Novelty Position:** The static resource allocation model is known in operations research as modular capacitated facility location. **The fundamental scientific contribution of this capstone project is the closed loop:** establishing that continuous empirical measurement, Bayesian reliability tracking, and decision-space drift detection make automated re-allocation necessary, while fast, predictable LP-repair heuristics make it computationally viable.
