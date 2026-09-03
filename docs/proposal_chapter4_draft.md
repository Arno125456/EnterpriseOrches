# Chapter 4: System Architecture, Semester 2 Implementation Plan, and Evaluation Methodology

**Senior Capstone Design Proposal**  
**Working Title:** Profile-Guided Multi-Workflow Resource Orchestration Platform  
**Authors:** Student IDs 035, 075, 077, 083, 089  
**Faculty Advisor:** Prof. Tossaphol  
**Date:** September 2026  

---

## 4.1 System Overview and Architectural Decomposition

The production platform is architected as a modular, decoupled microservices suite designed to sit between enterprise multi-agent workflow applications and physical GPU compute infrastructure.

```
+----------------------------------------------------------------------------------------------------+
|                                 APPLICATION LAYER (LangGraph / AutoGen)                            |
|             Workflow DAG 1 (RAG)               Workflow DAG 2 (Code Synthesis)                     |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                    [R9: Transport Proxy / API]
                                                  v
+----------------------------------------------------------------------------------------------------+
|                               CAPORCHES ORCHESTRATION SERVICE                                      |
|                                                                                                    |
|  +--------------------------------+                  +------------------------------------------+  |
|  | 1. DAG Ingestion & Validator   |                  | 5. Decision-Space Drift Detector (J8)     |  |
|  | - Parses task dependencies     |                  | - Evaluates compatibility C(A_new, A_old)|  |
|  | - Validates SLA floors (R, L)  |                  | - Triggers global re-allocation on C<0.9 |  |
|  +--------------------------------+                  +------------------------------------------+  |
|                 |                                                          ^                       |
|                 v                                                          |                       |
|  +--------------------------------+                  +------------------------------------------+  |
|  | 2. Candidate Filtering Engine  |                  | 4. Bayesian Profile Store (J6, J7)       |  |
|  | - UCB reliability filtering    |                  | - Decayed counting (gamma=0.995)         |  |
|  | - Latency ceiling gating       |                  | - Jeffreys prior Beta(0.5, 0.5)          |  |
|  +--------------------------------+                  +------------------------------------------+  |
|                 |                                                          ^                       |
|                 v                                                          |                       |
|  +--------------------------------+                  +------------------------------------------+  |
|  | 3. Fast Allocation Daemon (J4) |                  | [R7] Distributed Telemetry Collector     |  |
|  | - Track C (C+cons repair)      |                  | - OpenTelemetry / Prometheus streaming   |  |
|  | - Sub-100ms predictable solve  |                  | - Success/error, latency, token throughput| |
|  +--------------------------------+                  +------------------------------------------+  |
|                 |                                                          ^                       |
+-----------------|----------------------------------------------------------|-----------------------+
                  v                                                          |
+----------------------------------------------------------------------------------------------------+
|                            PHYSICAL INFRASTRUCTURE & EXECUTION LAYER                               |
|                                                                                                    |
|  +-----------------------------------------------+   +------------------------------------------+  |
|  | Kubernetes GPU Provisioning Controller (J5)   |   | [R8] Fallback & Circuit Breaker Engine   |  |
|  | - Scales worker pods (n[m] instances)         |   | - Immediate local retry on node timeout  |  |
|  | - Enforces cluster GPU budget (C3)            |   | - Graceful redirection under pod failure |  |
|  +-----------------------------------------------+   +------------------------------------------+  |
|                                                  |                                                 |
|          +----------------------+                +----------------------+                          |
|          | Commodity GPU Pool   |                | Standard / Premium   |                          |
|          | (e.g. 2x T4 / L4)    |                | (e.g. A100 / H100)   |                          |
|          +----------------------+                +----------------------+                          |
+----------------------------------------------------------------------------------------------------+
```

### 4.1.1 Component Responsibilities

1. **Workflow Ingestion Engine & DAG Validator (Jobs J1, J2):**
   * Exposes a declarative JSON/YAML workflow submission API.
   * Parses logical workflow structures into directed acyclic graphs, validating task dependencies and topological order.
   * Ingests task-level SLA requirements: throughput demand $d(t)$, reliability floor $R_{\min}(t)$ (anchored to baseline-delivered reliability), and latency ceiling $L_{\max}(t)$.

2. **Candidate Pool Filtering Engine (Job J3):**
   * Dynamically constructs the eligible candidate profile set $\mathcal{C}(t)$ for each task.
   * Enforces the **Upper Confidence Bound (UCB)** filtering rule (Finding **F25**), computing $\hat{r}(m) + z \cdot \sigma_r$ to prevent premature abandonment of cost-effective profiles caused by temporary observation noise.

3. **Joint Allocation Daemon (Jobs J4, J5):**
   * Houses our polynomial-time allocation algorithms: `C+cons` (Continuous LP relaxation with capacity consolidation repair) and `A+subset` (Lookahead greedy with subset-move neighborhood).
   * Generates discrete routing bindings $x[t][m] \in \{0, 1\}$ and physical provisioning counts $n[m] \in \mathbb{Z}^+$ adhering strictly to the cluster GPU budget $B$.
   * Executes in bounded, predictable sub-100ms time, ensuring zero stalls in the adaptation loop.

4. **Bayesian Profile Store & Telemetry Engine (Jobs J6, J7):**
   * Replaces volatile exponential moving averages with **Decayed Counting Estimators with Jeffreys Priors** (Finding **F19**), tracking successes and failures across a moving window of $N_{\text{eff}} \approx 200$ invocations.
   * Exposes real-time profile posterior parameters $(\hat{r}, \hat{\ell})$ to the candidate filter.

5. **Decision-Space Drift Detector (Jobs J8, J9):**
   * Implements the **Update Compatibility** metric $C(A_{\text{new}}, A_{\text{old}})$ grounded in *Hatherley (2025)* and *Bansal et al. (2019)*.
   * When updated profile statistics indicate that more than $10\%$ of routing decisions would flip ($C < 0.90$), a drift event is flagged, immediately triggering cluster-wide global re-allocation.

---

## 4.2 Semester 1 De-Risking via the Prototype

A frequent failure mode in senior engineering capstones is deferring core algorithmic and architectural unknowns to the second semester. In our project, **all core algorithmic mechanisms have already been implemented, experimentally benchmarked, and de-risked during Semester 1**:

| Requirement | Description | Semester 1 Status | Evidence / Verification |
|---|---|---|---|
| **R1** | Per-task model/hardware allocation | **Complete & Verified** | [`poc/formulation/types.py`](file:///D:/intern/EnterpriseOrches/poc/formulation/types.py), Invariant $I_1$ |
| **R2** | Multi-workflow aggregate coupling | **Complete & Verified** | Hand-verified adversarial fixture (`opt=280`), Finding F8 |
| **R3** | Non-exact polynomial alternatives to MILP | **Complete & Verified** | `C+cons` (<5% gap, 0.106s), `A+subset` (<3% gap), F17, F20 |
| **R4** | Self-updating Bayesian profiling | **Complete & Verified** | Decayed counting estimator in [`prototype/profiling.py`](file:///D:/intern/EnterpriseOrches/prototype/profiling.py), F19 |
| **R5** | Re-optimization on drift | **Complete & Verified** | Compatibility drift trigger in [`prototype/loop.py`](file:///D:/intern/EnterpriseOrches/prototype/loop.py), F24 |
| **R6** | Matched-condition evaluation vs. MILP | **Complete & Verified** | Tri-generator scale sweeps (8 to 64 tasks), [`docs/chapter3_benchmark_results.md`](file:///D:/intern/EnterpriseOrches/docs/chapter3_benchmark_results.md) |

All 646 automated tests pass with 100% green status. The foundational unknowns—algorithmic tractability, bound tightness, heuristic coupling, and Bayesian drift stability—are settled science.

---

## 4.3 Semester 2 Planned Scope: Engineering Unbuilt Requirements ($R_7, R_8, R_9$)

With the algorithmic foundations de-risked, Semester 2 focuses on constructing the production serving infrastructure, specifically targeting requirements **$R_7$**, **$R_8$**, and **$R_9$** from the project brief:

### 4.3.1 Requirement $R_7$: Distributed Execution Telemetry & Stream Monitoring
* **Motivation:** In Semester 1, the prototype validated Bayesian updating using injected synthetic observations. In Semester 2, observations must be extracted live from production model inference calls without introducing latency overhead.
* **Architecture:**
  * **OpenTelemetry Instrumentation:** We will embed lightweight, asynchronous telemetry interceptors into serving worker pods.
  * **Metrics Pipeline:** Interceptors stream Time-to-First-Token (TTFT), Time-per-Output-Token (TPOT), total generation latency, and HTTP status codes (200 OK vs. 429 Rate Limit / 504 Timeout) into a high-throughput Redis buffer.
  * **Asynchronous Ingestion Daemon:** A dedicated background worker consumes telemetry batches from Redis every 500 ms, updating the Bayesian Profile Store without stalling inference paths.

### 4.3.2 Requirement $R_8$: Execution-Time Reliability & Fallback Circuit Breakers
* **Motivation:** While global re-optimization resolves structural drift over multi-second horizons, individual task invocations can encounter transient server crashes or network partitions.
* **Architecture:**
  * **Per-Pod Circuit Breakers:** If an instance fails consecutive health checks, a local circuit breaker trips, temporarily removing the instance from the Level 1 router's active dispatch table.
  * **Local Fallback Rerouting:** In-flight tasks affected by a transient pod failure are automatically retried against the task's secondary eligible candidate in $\mathcal{C}(t)$ (the next cheapest compliant profile).
  * **Escalation to Global Re-Optimization:** If failures persist across multiple requests, the Bayesian profile reliability drops, tripping the decision compatibility threshold and triggering a full cluster re-solve.

### 4.3.3 Requirement $R_9$: Framework-Agnostic Multi-Agent Proxy Integration
* **Motivation:** Enterprise developers should not be forced to rewrite application logic or adopt proprietary agent frameworks to benefit from profile-guided orchestration.
* **Architecture:**
  * **Reverse-Proxy Design Pattern (*AgentOpt*, Hua et al., 2026):** We will build an OpenAI-compatible HTTP reverse proxy that intercepts outbound LLM API calls from standard frameworks (LangGraph, AutoGen, CrewAI, DSPy).
  * **Header-Based Metadata Tagging:** Workflows inject task identifiers and SLA constraints via standard HTTP headers (e.g., `X-CapOrches-Task-ID: doc_triage`, `X-CapOrches-Rel-Floor: 0.95`).
  * **Dynamic Request Routing:** The proxy queries the Level 1 routing table and transparently forwards the prompt to the provisioned physical worker instance serving that profile, returning the response seamlessly to the client application.

---

## 4.4 Semester 2 Evaluation Methodology & Benchmark Testbed

### 4.4.1 Workload Datasets and Workflow Generators

To establish publication-grade empirical validity, our Semester 2 evaluation will benchmark across three complementary workload tiers:
1. **Synthetic Multi-Workflow DAG Generators:**
   * Scaled evaluation extending from 64 to 256 tasks across our validated Uniform, Structured, and Heterogeneous instance generators.
   * Parameter sweeps evaluating budget tightness across $[0.6\times, 1.5\times B_{\text{ref}}]$.
2. **Representative Agentic Workflow Pipelines:**
   * **RAG Pipeline:** Document chunking $\to$ dense embedding $\to$ vector retrieval $\to$ multi-document synthesis $\to$ hallucination verification.
   * **Code Synthesis & Verification:** LLM-Debate pattern with specialized coder, unit-test generator, and reflective reviewer agents.
   * **Structured Document Triage:** High-throughput extraction and summarization over heterogeneous document batches.
3. **Real-World Trace Emulation:**
   * Ingesting production arrival traces from the **Azure LLM Serving Dataset (2024/2026)** and **LogHub Enterprise Traces** to simulate bursty request distributions and realistic multi-tenant contention.

### 4.4.2 Hardware Testbed Environment

The deployment target will be evaluated on a containerized GPU cluster:
* **Hardware Pool:** Local multi-GPU workstation / private cloud cluster equipped with NVIDIA A100 (80GB PCIe) and NVIDIA L4/T4 accelerators, providing a real heterogeneous hardware spread.
* **Serving Engines:** Containerized serving backends deploying open-weight enterprise LLMs (Llama-3-8B-Instruct, Mistral-7B, DeepSeek-Coder, and 4-bit/8-bit AWQ quantized variants) managed via vLLM and HuggingFace TGI.
* **Cluster Orchestration:** Lightweight Kubernetes (k3s) managing dynamic pod lifecycle and GPU device allocation via the NVIDIA Container Toolkit.

### 4.4.3 Comparative Baselines & Evaluation Metrics

We will evaluate CapOrches against three competitive baselines:
1. **Static Baseline:** Uncoordinated allocation where workflows independently select static model endpoints.
2. **Murakkab MILP Baseline:** Re-running exact mixed-integer programming on fixed 60-minute epochs without continuous telemetry updating.
3. **Open-Loop Greedy Baseline:** Constructive heuristic without drift feedback.

**Primary Evaluation Metrics:**
* **SLA Floor Compliance Rate:** Percentage of workflow tasks satisfying $r(m) \ge R_{\min}(t)$ and $\ell(m) \le L_{\max}(t)$ under active drift.
* **Total Provisioning Cost:** Aggregate dollar spend $\sum n[m] p(m)$ under matched throughput demand.
* **GPU Utilization Efficiency:** Ratio of active compute tokens served per provisioned GPU-hour.
* **Adaptation Latency & Overhead:** Wall-clock time required to detect drift and achieve stable re-allocation.

---

## 4.5 Semester 2 Project Timeline and Milestone Roadmap

```
+----------------------------------------------------------------------------------------------------+
|                                    SEMESTER 2 TIMELINE (WEEKS 1 - 16)                              |
+----------------------------------------------------------------------------------------------------+
| Weeks 1-4:   Infrastructure & Proxy Setup                                                          |
|              - Deploy Kubernetes GPU cluster testbed (vLLM on A100 / L4).                          |
|              - Build R9 OpenAI-compatible transport proxy for LangGraph/AutoGen interception.      |
+----------------------------------------------------------------------------------------------------+
| Weeks 5-8:   Telemetry Pipeline & Fallback Integration                                             |
|              - Build R7 OpenTelemetry distributed streaming metrics pipeline.                      |
|              - Integrate R8 per-pod circuit breakers and immediate local fallback retries.         |
|              - Wire live telemetry into Bayesian Profile Store (decayed counting).                 |
+----------------------------------------------------------------------------------------------------+
| Weeks 9-12:  System Integration & Scale Benchmarking                                                |
|              - Integrate Allocator Daemon (`C+cons` / `A+subset`) with live Kubernetes controller. |
|              - Execute multi-workflow scaling benchmarks across 64-256 tasks under drift.          |
+----------------------------------------------------------------------------------------------------+
| Weeks 13-16: Empirical Evaluation, Paper Writing & Final Capstone Defense                          |
|              - Execute matched-condition comparison against Murakkab and Static baselines.         |
|              - Author final Capstone Thesis and prepare M2/M3 defense presentation.                |
+----------------------------------------------------------------------------------------------------+
```

---

## 4.6 Risk Analysis and Mitigation Matrix

| Identified Risk | Likelihood | Impact | Engineered Mitigation Strategy |
|---|---|---|---|
| **GPU Hardware Constraints** | Medium | Medium | Testbed is containerized and hardware-agnostic; fallback to cloud GPU instances (GCP/RunPod) or synthetic GPU emulation if physical hardware is constrained. |
| **Telemetry Noise Volatility** | Low | High | **Eliminated in PoC:** Bayesian decayed counting with Jeffreys prior ($N_{\text{eff}}=200$) and UCB candidate filtering prevent noise-induced oscillation (Findings F19, F25). |
| **Solver Scaling & Timeouts** | Low | High | **Eliminated in PoC:** `C+cons` provides bounded runtime (0.106s at 128 tasks, F29); CBC solver is bounded with explicit timeout limits (F28). |
| **Framework Incompatibility** | Low | Medium | R9 reverse-proxy adheres strictly to standard OpenAI REST/v1 completions schema, ensuring universal compatibility without client-side modifications. |
| **Formulation Dispute at T0** | Low | Low | Fully addressed via [`docs/T0_Formulation_Ratification_Briefing.md`](file:///D:/intern/EnterpriseOrches/docs/T0_Formulation_Ratification_Briefing.md) detailing the MCFLP-B formulation and SLA floor rationale. |
