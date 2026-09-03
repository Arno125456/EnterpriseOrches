# CapOrches: Profile-Guided Multi-Workflow Resource Orchestration Platform

**Senior Capstone Design Project Proposal — Milestone M1**  
**Department of Computer Engineering, Faculty of Engineering**  
**Academic Year 2026–2027**  

**Student Project Team:**  
* Student ID 035 — Lead & Heuristic Search
* Student ID 075 — Mathematical Programming & Duality
* Student ID 077 — Systems Architecture & Telemetry
* Student ID 083 — Software Engineering & Instance Modeling
* Student ID 089 — Empirical Methodology & Statistical Verification  

**Faculty Advisor:** Prof. Tossaphol  
**Date of Submission:** September 2026  

---

## Executive Summary

Enterprise cloud software is undergoing a generational shift: monolithic single-model Large Language Model (LLM) queries are rapidly being replaced by multi-stage, collaborative agentic workflows structured as Directed Acyclic Graphs (DAGs). These workflows combine specialized models, retrieval engines, and verification loops. In private enterprise clouds, High-Bandwidth Memory (HBM) GPU accelerators (e.g., NVIDIA A100, H100) are strictly limited and expensive. Today, existing workflow frameworks treat model selection and hardware provisioning as uncoordinated local choices, resulting in severe GPU fragmentation, premature quota exhaustion, and budget collapse.

State-of-the-art systems such as *Murakkab* (OSDI '26) formulate joint model selection and hardware provisioning as an offline Mixed-Integer Linear Program (MILP), but assume that serving parameters (latency, throughput, and reliability) are static, declared constants. In production, serving parameters drift continuously due to dynamic multi-tenant contention, variable prompt contexts, and network timeouts. Under empirical drift, **a static allocator silently breaches enterprise SLA floors (delivering 0.542 reliability against a 0.95 floor), completely blind to ongoing failures.**

This project designs, implements, and evaluates **CapOrches**, an adaptive, profile-guided orchestration platform. CapOrches operates as a robust closed loop:
1. Continuously measures execution telemetry, updating profile parameters using a **Decayed Counting Estimator with Jeffreys Prior** ($\text{Beta}(0.5, 0.5)$) that eliminates artificial reliability ceilings.
2. Filters candidate profiles using an **Upper Confidence Bound (UCB)** rule that recovers the exact optimum ($400.0$ cost) without noise-induced overpayment.
3. Detects decision-relevant drift via **Update Compatibility** $C(A_{\text{new}}, A_{\text{old}})$, triggering cluster-wide re-allocation only when $>10\%$ of routing decisions flip.
4. Solves the underlying Modular Capacitated Facility Location Problem with Budget Constraints (MCFLP-B) using **Track C (`C+cons`)**, a continuous LP relaxation with multi-move capacity consolidation repair that executes in a predictable **0.106 ± 0.020 seconds** with a **3.03 ± 1.62% optimality gap** at 128 tasks, eliminating exact solver heavy tails.

Empirical validation across 646 automated tests proves that while static allocation fails under drift, CapOrches preserves reliability floors (**0.938 delivered, yielding a paired benefit of +0.424 [0.405, 0.442]**, $n=20$).

---

# Table of Contents
1. [Chapter 1: Introduction, Problem Formulation, and Objectives](#chapter-1-introduction-problem-formulation-and-objectives)
2. [Chapter 2: Literature Review and Theoretical Positioning](#chapter-2-literature-review-and-theoretical-positioning)
3. [Chapter 3: Empirical Validation, Proof-of-Concept, and Algorithmic Architecture](#chapter-3-empirical-validation-proof-of-concept-and-algorithmic-architecture)
4. [Chapter 4: System Architecture, Semester 2 Implementation Plan, and Evaluation Methodology](#chapter-4-system-architecture-semester-2-implementation-plan-and-evaluation-methodology)
5. [References](#references)

---

# Chapter 1: Introduction, Problem Formulation, and Objectives

## 1.1 Context and Motivation: The Enterprise LLM Resource Dilemma

Enterprise software systems are undergoing a rapid architectural transition: monolithic single-prompt Large Language Model (LLM) queries are being replaced by **multi-stage agentic workflows** structured as Directed Acyclic Graphs (DAGs). These pipelines—spanning document extraction, multi-agent debate, code synthesis, iterative verification, and Retrieval-Augmented Generation (RAG)—require executing sequences of heterogeneous specialized tasks.

In enterprise private clouds and managed compute clusters, hardware resources—specifically High-Bandwidth Memory (HBM) accelerators such as NVIDIA A100 and H100 GPUs—are scarce, expensive, and subject to strict aggregate budgetary caps. When multiple enterprise departments submit concurrent workflow DAGs against a shared cluster, an orchestrator must make two fundamentally coupled decisions:
1. **Level 1 (Logical Routing):** Which serving profile (model architecture, quantization level, and execution backend) should be assigned to execute each logical workflow task?
2. **Level 2 (Physical Provisioning):** Exactly how many discrete physical server instances of each serving profile should be provisioned to satisfy aggregate throughput demand without exceeding the cluster's GPU budget?

Today, enterprise workflow frameworks (e.g., LangGraph, AutoGen, CrewAI) treat these decisions as disconnected, ad-hoc choices. Individual application developers select model endpoints statically, typically choosing oversized flagship models (e.g., 70B parameters on 4×A100 instances) to guarantee output quality. When deployed across a multi-tenant cluster, uncoordinated provisioning results in catastrophic resource fragmentation: instances sit 60–80% under-utilized, GPU quotas are exhausted prematurely, and concurrent critical tasks are stranded.

## 1.2 Problem Statement: Why Static Allocation Fails Under Drift

State-of-the-art cloud orchestration platforms, such as *Murakkab* (Chaudhry et al., *OSDI '26*), formulate joint model selection and hardware provisioning as an offline Mixed-Integer Linear Program (MILP). While this achieves significant static cost savings over uncoordinated baselines, it relies on a foundational assumption that breaks in production: **that profile performance parameters (latency, throughput, and reliability) are static, declared constants.**

In real-world serving environments, empirical parameters **drift continuously**:
1. **Non-Stationary Reliability:** Upstream prompt variability, non-deterministic token lengths, context-window overflow, and backend connection timeouts cause empirical task success rates to deviate significantly from vendor benchmarks.
2. **Dynamic Latency Fluctuations:** Multi-tenant memory bus contention, noisy neighbors, and KV-cache thrashing introduce unpredictable latency spikes.
3. **The Static Allocation Breakdown:** Under empirical drift, a static allocator that solves the provisioning problem once at admission operates open-loop. As proven in our empirical findings (Finding **F24**), **a static allocator silently breaches enterprise SLA floors (delivering an empirical reliability of 0.542 against a declared 0.95 floor), completely blind to ongoing failure.**

Simply re-solving the allocation via an exact solver upon every telemetry event is computationally intractable. Exact mixed-integer solvers scale poorly: at 128 tasks, exact MILP exhibits heavy-tailed runtimes averaging **12.3 ± 10.3 seconds**, with adversarial instances running for minutes or hanging without timeouts (Finding **F13**, **F29**). A high-frequency telemetry loop cannot tolerate an optimizer that periodically stalls.

## 1.3 Project Objectives and Research Questions

To resolve this dilemma, this project designs, implements, and evaluates the **Profile-Guided Multi-Workflow Resource Orchestration Platform (CapOrches)**. The platform operates as a robust closed loop: continuously measuring empirical execution telemetry, maintaining Bayesian profile estimates, detecting decision-relevant drift, and triggering global re-allocation via a fast, predictable solving engine.

### Research Questions ($T_0–T_4$)
* **$T_0$ (Mathematical Formulation):** Can joint task routing and instance provisioning under hard GPU budgets and SLA floors be formulated as a rigorous, solvable mathematical program?
* **$T_1$ (Lagrangian Duality & Optimality Certificates):** Does Lagrangian relaxation of unit assignment ($C_1$) or budget ($C_3$) produce tractable, high-quality dual lower bounds to certify solution quality?
* **$T_2$ (Heuristic Foundations):** Can constructive greedy heuristics find near-optimal allocations, or does aggregate capacity coupling across shared instances create structural failure modes?
* **$T_3$ (Budget Operating Regimes):** How does the cluster GPU budget cap constrain the feasible operating region, and where do heuristic phase transitions occur?
* **$T_4$ (Regime-Dependent Solving):** Under what scale and tightness conditions is heuristic solving justified over exact MILP or continuous LP relaxation?

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

## 2.1 Scope of the Literature Review

Our theoretical framework synthesizes twelve foundational research papers categorized across three core scopes:
* **Scope $S_1$ (Workflow Orchestration & Declarative DAGs):** Systems decoupling logical pipeline specifications from physical execution environments.
* **Scope $S_2$ (Resource Allocation, Routing, & Optimization):** Algorithmic mechanisms for task-to-model-to-hardware assignment under capacity constraints.
* **Scope $S_3$ (Empirical Methodology & Evaluation):** Experimental design, drift detection, and statistical validation in non-stationary ML serving.

## 2.2 Workflow Orchestration Systems ($S_1$)

### 2.2.1 Declarative Pipelines and Logical-Physical Decoupling
Traditional agentic frameworks—including LangChain, AutoGen (*Wu et al., 2023*), and CrewAI—tightly couple prompt engineering with physical model endpoints. Developers hard-code specific model identifiers (e.g., `gpt-4o` or `claude-3-5-sonnet`) directly into individual agent functions.

*DSPy* (*Khattab et al., ICLR 2024, Paper P12*) introduced the foundational principle of **separating declarative pipeline structure from execution parameter optimization**. In DSPy, workflows are expressed as typed modular programs; an automated compiler optimizes prompt instructions and demonstration few-shot examples against formal metric evaluators. 

Our architecture extends this separation of concerns to **systems-level infrastructure**:
* Application developers specify **logical workflow DAGs** with declarative task requirements (throughput demand, latency ceilings $L_{\max}$, and reliability floors $R_{\min}$).
* The platform's allocation engine independently determines the **physical realization**: mapping logical tasks to concrete serving profiles and provisioning GPU worker pools.

## 2.3 Resource Allocation and Serving Optimization ($S_2$)

### 2.3.1 Mixed-Integer Linear Programming in Cloud Serving: Murakkab
*Murakkab* (*Chaudhry et al., OSDI '26, Paper P1*) established the benchmark for multi-tenant agentic workflow orchestration in cloud platforms. Murakkab addresses combinatorial configuration spaces by mapping workflows to a logical DAG, profiling models ahead of time, and solving a centralized Mixed-Integer Linear Program (MILP) using Gurobi with a 300-second time limit.

Murakkab demonstrated that cross-workflow instance colocation and multiplexing reduces GPU usage by up to 2.8× and dollar costs by up to 4.3×. However, Murakkab operates on a coarse, periodic optimization epoch (e.g., 60 minutes) and assumes profile parameters are static inputs. Our work differs fundamentally:
1. **Cadence and Responsiveness:** Rather than waiting for a 60-minute batch window, our system continuously monitors execution telemetry and triggers immediate re-allocation upon detecting decision-relevant drift.
2. **Computational Tractability:** Rather than relying on commercial exact solvers with multi-minute timeouts, we provide polynomial-time heuristics (`C+cons`) delivering bounded runtimes under 100 milliseconds.

### 2.3.2 Constructive Heuristics & Activation Ranking: Cheng & Nguyen
*Cheng & Nguyen* (*arXiv:2604.07472, 2026, Paper P3*) proposed constructive heuristic frameworks for multi-workflow allocation, introducing greedy activation-cost ranking and lookahead feasibility filtering (`C_FEASFIRST`).

In our research, we evaluated whether constructive greedy methods can serve as the primary allocator. In Finding **F8**, we proved that plain greedy heuristics are structurally defeated on adversarial instances due to **aggregate capacity coupling**: when multiple tasks share a single provisioned instance, sequential greedy placement cannot see the joint cost reduction of moving multiple tasks simultaneously. We resolved this fundamental limitation by designing the **subset consolidation neighborhood (`A+subset`)**, which evaluates simultaneous relocations of task subsets ($k \le 2$), achieving global optimality on coupled fixtures.

## 2.4 Drift, Uncertainty, and Opacity in Machine Learning Systems

### 2.4.1 Update Opacity and Update Compatibility: Hatherley & Bansal et al.
A critical theoretical challenge in adaptive systems is understanding the operational impact of continuous updates. *Hatherley* (*2025, Ethics and Information Technology, Paper P9*) investigated **update opacity**—the inability of users to predict or explain why an updated ML model produces a different decision than its predecessor on functionally identical inputs. This causes *intra-ML disagreement* (diachronic evolution over time), disrupting learned trust and operational workflows.

Hatherley evaluated mitigation strategies, formalizing the concept of **Update Compatibility** following *Bansal et al.* (*2019, Updates in AI*). Update compatibility measures the fraction of decisions preserved across an update:
$$C(h_2, h_1) = \frac{|\{x \in \mathcal{D} \mid h_2(x) = h_1(x)\}|}{|\mathcal{D}|}$$

We operationalize this literature concept in our **Drift Detection Engine**:
$$\text{Compatibility}(A_{\text{new}}, A_{\text{old}}) = \frac{|\{t \in \mathcal{T} \mid A_{\text{new}}(t) = A_{\text{old}}(t)\}|}{|\mathcal{T}|}$$
Rather than triggering re-optimization on raw parameter shifts that would not alter physical routing, our engine evaluates compatibility in the **discrete decision space**. Re-allocation is triggered only when compatibility drops below a tuned threshold (e.g., $\tau = 0.90$), preventing unnecessary cluster churn and minimizing update opacity.

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

## 2.6 The Novelty Boundary Matrix (Advisor Question O12)

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

---

# Chapter 3: Empirical Validation, Proof-of-Concept, and Algorithmic Architecture

## 3.1 Formal MCFLP-B Problem Formulation ($T_0$)

Joint task routing and instance provisioning is formalized as:
$$\min_{x, n} \quad \sum_{m \in \mathcal{M}} n[m] \cdot p(m)$$
subject to:
$$\sum_{m \in \mathcal{C}(t)} x[t][m] = 1 \quad \forall t \in \mathcal{T} \tag{C1: Unit Assignment}$$
$$\sum_{t \in \mathcal{T}} x[t][m] \cdot d(t) \le n[m] \cdot u(m) \quad \forall m \in \mathcal{M} \tag{C2: Capacity Coverage}$$
$$\sum_{m \in \mathcal{M}} n[m] \cdot g(m) \le B \tag{C3: Cluster GPU Budget Cap}$$
$$x[t][m] \in \{0, 1\}, \quad n[m] \in \{0, 1, 2, \dots\}$$
where $\mathcal{C}(t) = \{m \in \mathcal{M} \mid r(m) \ge R_{\min}(t) \wedge \ell(m) \le L_{\max}(t)\}$.

## 3.2 Adaptive Closed-Loop Telemetry Under Drift

### 3.2.1 Decayed Counting Estimator with Jeffreys Prior (Finding F19)
Traditional Exponential Moving Averages (EMA) fail for binary reliability estimation ($x \in \{0, 1\}$). EMA with $\alpha=0.3$ plunges estimated reliability from 0.99 to 0.69 on a single failure, and an aggressive decay ($\gamma=0.98, N=50$) imposes an artificial ceiling of $0.981$, permanently barring tasks demanding $0.99$ reliability.

We deployed a Decayed Counting Estimator with Jeffreys Prior ($\text{Beta}(0.5, 0.5)$):
$$S_{k} = \gamma S_{k-1} + y_k, \quad F_{k} = \gamma F_{k-1} + (1 - y_k), \quad \hat{r} = \frac{S_k + 0.5}{S_k + F_k + 1.0}$$
Setting $\gamma = 0.995$ yields an effective sample size of $N_{\text{eff}} \approx 200$, providing an achievable ceiling of $0.9975$ while smoothing out transient observation noise.

### 3.2.2 The Core Differentiator: Static Failure vs. Adaptive Protection (Finding F24)
Under controlled synthetic drift across 20 random seeds:
* **Static Baseline:** Delivered empirical reliability of **0.542 ± 0.018**, severely breaching the 0.95 SLA floor.
* **CapOrches Adaptive Loop:** Maintained **0.938 ± 0.012** reliability.
* **Paired Benefit:** **+0.424 [0.405, 0.442]** (95% CI, $n=20$).

### 3.2.3 Candidate Filtering via Upper Confidence Bound (Finding F25)
Filtering $\mathcal{C}(t)$ via point estimates causes a permanent 40% cost overpayment (median cost 560 vs. optimum 400). UCB filtering ($\hat{r} + z \sigma_r$) recovered the exact optimum of **400.0 with zero variance** across all 20 seeds.

## 3.3 Why Re-Optimization Must Be Global (Finding F18)
Measuring multi-workflow profile overlap across concurrent pipelines revealed that shared profile instances are utilized by **84% to 100%** of concurrent workflows. Consequently, local or scoped re-optimization is vacuous: a change to any drifted profile ripples across the capacity of the entire cluster. Re-optimization must be executed globally.

## 3.4 Multi-Scale Benchmark Results (8 to 64 Tasks)

Evaluated at $1.25\times B_{\text{ref}}$ across matched random seeds:

| Generator | Scale | Condition | Feasible | Opt Match | Mean Gap (%) | Max Gap (%) | Bound Gap (%) | Runtime (s) |
|---|---|---|---|---|---|---|---|---|
| **Uniform** | 8t, 4p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.026 |
| | 8t, 4p | **A+subset** | 5/5 | 4 | 4.51% | 22.53% | - | 0.000 |
| | 8t, 4p | **C+cons** | 5/5 | 2 | 8.73% | 22.53% | 14.32% | 0.020 |
| | 16t, 6p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.083 |
| | 16t, 6p | **A+subset** | 5/5 | 3 | 3.27% | 14.96% | - | 0.003 |
| | 16t, 6p | **C+cons** | 5/5 | 0 | 9.50% | 17.33% | 7.67% | 0.025 |
| | 32t, 8p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.214 |
| | 32t, 8p | **A+subset** | 5/5 | 1 | 2.20% | 4.61% | - | 0.013 |
| | 32t, 8p | **C+cons** | 5/5 | 1 | 3.97% | 7.93% | 1.82% | 0.039 |
| | 64t, 10p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 9.821 |
| | 64t, 10p | **A+subset** | 5/5 | 0 | 4.78% | 8.95% | - | 0.070 |
| | 64t, 10p | **C+cons** | 5/5 | 0 | 4.00% | 8.84% | 1.37% | 0.050 |
| **Structured** | 32t, 8p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.153 |
| | 32t, 8p | **A (Plain)** | 2/5 | 0 | 27.95% | 34.52% | - | 0.001 |
| | 32t, 8p | **A+subset** | 3/5 | 0 | 13.15% | 22.61% | - | 0.031 |
| | 32t, 8p | **C+cons** | 5/5 | 1 | 8.02% | 17.86% | 6.07% | 0.049 |
| | 64t, 10p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.210 |
| | 64t, 10p | **C+cons** | 5/5 | 0 | 5.59% | 10.70% | 3.09% | 0.063 |
| **Heterogeneous** | 32t, 8p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 0.243 |
| | 32t, 8p | **STATIC** | 0/5 | 0 | - | - | - | 0.000 |
| | 32t, 8p | **C+cons** | 5/5 | 1 | 4.10% | 15.17% | 2.48% | 0.041 |
| | 64t, 10p | **MILP** | 5/5 | 5 | 0.00% | 0.00% | 0.00% | 1.065 |
| | 64t, 10p | **STATIC** | 0/5 | 0 | - | - | - | 0.000 |
| | 64t, 10p | **C+cons** | 3/5 | 0 | 1.52% | 3.90% | 1.67% | 0.056 |

### 3.5 Heterogeneous Fleet Dynamics (Findings F31 & F32)
In real enterprise clouds, price is not proportional to GPU count. On our heterogeneous generator (`corr = -0.0105`), relaxing the GPU budget from 4 to 6 GPUs allows the solver to shift load from expensive Premium instances to Commodity instances, saving **$50.93 (5.0%) in operating expense**. The GPU budget constraint $(C_3)$ actively shapes optimal cost.

---

# Chapter 4: System Architecture, Semester 2 Implementation Plan, and Evaluation Methodology

## 4.1 Production System Architecture

The CapOrches production architecture comprises:
1. **Workflow Ingestion & DAG Validator (J1, J2):** Parses declarative JSON/YAML pipelines, validating dependencies and SLA floors.
2. **Candidate Pool Filtering Engine (J3):** Computes UCB reliability bounds and gates latency ceilings.
3. **Joint Allocation Daemon (J4, J5):** Executes `C+cons` in <100ms, outputting routing $x[t][m]$ and instance counts $n[m]$.
4. **Bayesian Profile Store (J6, J7):** Manages posterior parameters via decayed counting ($\gamma=0.995, \text{Beta}(0.5, 0.5)$).
5. **Decision-Space Drift Detector (J8, J9):** Monitors routing compatibility $C(A_{\text{new}}, A_{\text{old}})$, triggering re-allocation on $C < 0.90$.

## 4.2 Semester 2 Planned Scope ($R_7, R_8, R_9$)

| Requirement | Module | Functionality |
|---|---|---|
| **$R_7$ Distributed Telemetry** | OpenTelemetry streaming pipeline | Asynchronously collects TTFT, TPOT, and error codes into Redis buffer every 500ms. |
| **$R_8$ Runtime Reliability** | Circuit breakers & local fallback | Intercepts pod timeouts; executes immediate local retry on secondary compliant profile before global re-solve. |
| **$R_9$ Framework Proxy** | OpenAI-compatible HTTP proxy | Intercepts LangGraph, AutoGen, and CrewAI API calls via header metadata without application code changes. |

## 4.3 Evaluation Testbed and Workload Methodology

* **Hardware Testbed:** Local multi-GPU workstation / private cloud cluster equipped with NVIDIA A100 and L4 GPUs running lightweight Kubernetes (k3s).
* **Serving Engines:** Open-weight enterprise LLMs (Llama-3-8B-Instruct, Mistral-7B, DeepSeek-Coder) served via vLLM and AWQ quantization.
* **Workloads:** Real-world request arrival traces from Azure LLM Serving Traces and LogHub enterprise logs across RAG, Code-Gen, and Document Triage pipelines.
* **Comparative Baselines:** Evaluated against Static Allocation, Murakkab 60-minute Epoch MILP, and Open-Loop Heuristics.

## 4.4 Semester 2 Timeline & Milestones

* **Weeks 1–4:** Deploy Kubernetes GPU testbed; implement R9 OpenAI reverse proxy.
* **Weeks 5–8:** Construct R7 OpenTelemetry pipeline; integrate R8 circuit breakers and live Bayesian store updates.
* **Weeks 9–12:** Wire Allocator Daemon with Kubernetes pod controller; execute 64–256 task scaling sweeps.
* **Weeks 13–16:** Execute comparative benchmark evaluation vs. Murakkab; complete final capstone thesis and defense.

---

# References

1. Chaudhry, G. I., Choukse, E., Qiu, H., Goiri, I., Fonseca, R., Belay, A., & Bianchini, R. (2026). *Murakkab: Resource-Efficient Agentic Workflow Orchestration in Cloud Platforms.* Proceedings of the 20th USENIX Symposium on Operating Systems Design and Implementation (OSDI '26), pp. 567–587. arXiv:2508.18298.
2. Cheng, X., & Nguyen, T. (2026). *Multi-Workflow Resource Allocation and Model Assignment in Heterogeneous Computing Clusters.* arXiv:2604.07472.
3. Khattab, O., Singhvi, A., Maheshwari, P., Zhang, Z., Santhanam, K., Vardhamanan, S., Haq, R., Sharma, A., Joshi, T. T., Moazam, H., Miller, H., Zaharia, M., & Potts, C. (2024). *DSPy: Compiling Declarative Language Model Calls into State-of-the-Art Pipelines.* International Conference on Learning Representations (ICLR 2024).
4. Hatherley, J. (2025). *A moving target in AI-assisted decision-making: dataset shift, model updating, and the problem of update opacity.* Ethics and Information Technology, 27, 20.
5. Bansal, G., Nushi, B., Kamar, E., Lasecki, W. S., Tan, C., & Horvitz, E. (2019). *Updates in AI: Evaluating and Improving Updates of Machine Learning Models.* Proceedings of the AAAI Conference on Human Computation and Crowdsourcing (HCOMP 2019).
6. Geoffrion, A. M. (1974). *Lagrangian Relaxation for Integer Programming.* Mathematical Programming Study, 2, 82–114.
7. Fisher, M. L. (1981). *The Lagrangian Relaxation Method for Solving Integer Programming Problems.* Management Science, 27(1), 1–18.
8. Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2023). *AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation.* arXiv:2308.08155.
9. Hua, W., et al. (2026). *AgentOpt: Transport-Layer Interception and Optimization for Multi-Agent Systems.* arXiv:2602.11450.
