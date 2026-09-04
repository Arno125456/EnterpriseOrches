# T0 Formulation Ratification Session: Role Briefing & Advisor Defense Checklist

**Target Session Date:** 8 September 2026  
**Milestone:** $T_0 / D_1$ (Mathematical Formulation Ratification)  
**Stakeholders:** Prof. Tossaphol (Advisor), Student Roles (035 Lead, 075 Math, 077 Systems, 083 Software, 089 Methodology)  
**Primary References:** [`docs/System_Architecture_v2.md`](System_Architecture_v2.md) §1, [`docs/T0_Formulation_Ratification_Briefing.md`](T0_Formulation_Ratification_Briefing.md), [`docs/T0_Ratification_Signoff_Record.md`](T0_Ratification_Signoff_Record.md)

---

## 1. 30-Minute Meeting Agenda & Protocol

| Time | Duration | Agenda Item | Lead Speaker | Deliverable / Artifact |
|---|---|---|---|---|
| **00:00 - 05:00** | 5 min | **Executive Framing & Advisor Mandate Check** | **035 (Lead)** | Slide deck / Briefing §1 |
| **05:00 - 12:00** | 7 min | **Mathematical Programming Model ($T_0$) & Option A Defense** | **075 (Math) & 083 (Eng)** | Architecture §1, Briefing §2–§4 |
| **12:00 - 18:00** | 6 min | **Empirical Proof & The Closed-Loop Differentiator (F24)** | **077 (Sys) & 089 (Method)** | Timeline figure / Briefing §5 |
| **18:00 - 25:00** | 7 min | **Live Pre-Flight Verifier Execution & Advisor Q&A** | **All Roles** | `scripts/verify_t0_readiness.py` |
| **25:00 - 30:00** | 5 min | **Formal Attestation & Sign-Off Ratification** | **Prof. Tossaphol & Team** | `docs/T0_Ratification_Signoff_Record.md` |

---

## 2. Per-Role Rehearsal Scripts & Exact Talking Points

### Role 035 (Project Lead & Heuristics)
* **Opening Mandate (00:00):**
  > *"Good afternoon, Prof. Tossaphol. The purpose of today’s session is formal ratification of our Milestone $T_0$ mathematical formulation. Over the past month, our team has transformed our architectural concept into a mathematically proven, fully verified platform across 654 automated tests. Today, we present the ratified formulation, demonstrate that our five core invariants hold across all solvers, and ask for your formal sign-off to proceed into Semester 2 implementation."*
* **Heuristic Role Defense (10:00):**
  > *"On the algorithmic front, we proved in Finding F20 that greedy heuristics suffer from aggregate capacity coupling on shared profiles. We solved this by developing subset consolidation (`A+subset`), which evaluates simultaneous relocations of task pairs ($k \le 2$), achieving the hand-calculated global optimum of 280 on our adversarial fixture in under 15ms."*

---

### Role 075 (Mathematical Programming & Dual Theory)
* **Formulation & Classification Defense (05:00):**
  > *"Prof. Tossaphol, our formulation in Section 1 models joint task routing and hardware provisioning as a Modular Capacitated Facility Location Problem with a Global Budget Constraint (MCFLP-B). We minimize dollar provisioning cost $\sum n_m p_m$ subject to unit assignment $(C_1)$, modular capacity coverage $(C_2)$, and cluster GPU budget $(C_3)$. Decision variables are strictly partitioned: $x[t][m]$ is binary logical routing, and $n[m]$ is integer physical instance provisioning."*
* **Duality Hierarchy & Tractability (08:00):**
  > *"To certify solution quality, we evaluated both continuous LP relaxation (Track C) and Lagrangian relaxation (Track B). In Finding F30, we proved that dualizing assignment constraint $(C_1)$ decouples the problem into independent 0/1 knapsacks per profile, producing lower bounds that are 12.57 percentage points closer to the true optimum than the LP bound. Furthermore, by vectorizing the knapsack dynamic program via NumPy slice operations (Finding F33), we cut solve time from 7.16s down to 0.062s—a 115× speedup—making duality bounds viable at runtime."*

---

### Role 083 (Software Engineering & Invariant Gatekeeper)
* **Defending Option A: Hard SLA Floors vs. Multi-Objective (07:00):**
  > *"A key architectural decision was whether reliability should be a multi-objective term ($\min \text{Cost} - \lambda \cdot \text{Rel}$) or a hard feasibility gate. We strongly recommend Option A: hard SLA floors. In enterprise clouds, SLAs are legal contracts: exceeding 99.5% reliability yields zero business utility, while dropping to 98% is an outage. Treating reliability as a feasibility filter keeps the optimization problem a clean single-objective facility location model, eliminates arbitrary dollar-to-reliability trade-off hyperparameters ($\lambda$), and follows premier literature including Murakkab (OSDI '26)."*
* **Heterogeneous Hardware Decorrelation (Finding F32):**
  > *"Our heterogeneous fleet generator reflects real cloud pricing tiers (Commodity T4, Standard A100, Premium H100). In homogeneous clusters where price is linear in GPUs, $(C_3)$ is redundant. On our heterogeneous generator, price is decorrelated from GPU count ($\text{corr} = -0.0105$). This activates $(C_3)$, proving that relaxing the GPU budget from 12 to 24 GPUs allows consolidating onto high-density premium instances, saving $180.16 (4.90%) in operating expense."*

---

### Role 077 (Systems Architecture & Closed-Loop Integration)
* **The Core Differentiator: Open-Loop Failure vs. Adaptive Loop (12:00):**
  > *"Prof. Tossaphol, the core scientific thesis of CapOrches is that open-loop orchestration is fundamentally broken under drift. State-of-the-art schedulers like Murakkab assume serving parameters are static constants. In production, parameter drift is inevitable due to contention and prompt variance. In Finding F24, we proved that a static allocator silently fails: its delivered reliability crashes to 0.560 against a 0.95 floor, completely unaware of ongoing failure. CapOrches operates closed-loop: our decayed counting estimator ($\gamma=0.995, \text{Beta}(0.5, 0.5)$) tracks reality and triggers global re-allocation when decision compatibility drops below 0.90, preserving 0.995 reliability."*
* **Sub-Second Repair Engine (`C+cons`):**
  > *"To ensure runtime re-allocation is viable, we optimized Track C (`C+cons`) with memoized instance headroom vector caching. Candidate move evaluation dropped from $O(\|T\|)$ full-fleet scans to $O(1)$ scalar arithmetic. On 64 tasks, repair runtime dropped from 114.8ms to 13.76ms (8.3× speedup), guaranteeing sub-second responsiveness without exact solver heavy tails."*

---

### Role 089 (Empirical Methodology & Statistical Rigor)
* **Statistical Rigor & Paired Confidence Intervals (15:00):**
  > *"In accordance with senior capstone guidelines, we do not report raw ratios of means. Every performance claim is evaluated across 20 matched random seeds and reported as paired differences with 95% Confidence Intervals. Under matched drift, CapOrches delivers a steady-state paired reliability gain of +0.434 [0.410, 0.458] ($p < 10^{-12}$) and a cumulative 12-round gain of +0.424 [0.405, 0.442]."*
* **UCB Filtering Proof (Finding F25):**
  > *"We also evaluated candidate pool construction. In Finding F25, we showed that naive point-estimate filtering causes a permanent 40% cost overpayment because single noisy observations disqualify cheap profiles. Replacing it with an Upper Confidence Bound (UCB) filter recovered the true optimal cost of $400.0 with zero variance across all 20 seeds."*

---

## 3. Advisor Challenge Anticipation Matrix (Defense Drills)

### Challenge 1: "Why shouldn't we formulate reliability as an objective function term?"
* **Target Respondent:** Role 083 / Role 075
* **Defensible Answer:**
  > *"In enterprise production, workflows operate under strict Service Level Agreements (SLAs). Violating an SLA triggers financial penalties or system outages, whereas exceeding the floor provides negligible marginal benefit. If we placed reliability in the objective as $\text{Cost} - \lambda \cdot \text{Rel}$, we would introduce a scalar hyperparameter $\lambda$ with no natural physical units (\$/percentage). Furthermore, an objective term allows a high reliability on a non-critical background task to compensate for an SLA violation on a critical user-facing task. Option A guarantees that every task strictly satisfies $R_{\min}(t)$ by construction while keeping the optimization problem a clean single-objective integer program with rigorous dual bounds."*

### Challenge 2: "Could high-frequency telemetry updates cause allocation thrashing?"
* **Target Respondent:** Role 077
* **Defensible Answer:**
  > *"We built two architectural dampeners to completely eliminate thrashing:
  > 1. **Temporal Filtering:** Our Decayed Counting Estimator uses a decay factor $\gamma = 0.995$, giving an effective observation window of $N_{\text{eff}} \approx 200$ samples. Transient spikes or isolated packet drops are smoothed out and cannot trigger sudden state changes.
  > 2. **Decision-Space Drift Gating ($J_8$):** Rather than re-allocating whenever a profile parameter changes by $\epsilon$, our drift detector monitors Update Compatibility $C(A_{\text{new}}, A_{\text{old}})$. Re-allocation is suppressed unless the drifted belief causes $>10\%$ of logical routing decisions to flip ($C < 0.90$)."*

### Challenge 3: "Why not use an existing system like Ray Serve or Kubernetes HPA?"
* **Target Respondent:** Role 035 / Role 077
* **Defensible Answer:**
  > *"Ray Serve and Kubernetes Horizontal Pod Autoscaling (HPA) are horizontal execution engines—they scale replicas of an already-selected model profile based on CPU/GPU utilization or queue depth. They do not solve the joint problem: selecting which model profile satisfies task-level accuracy and latency SLAs, while determining the minimal number of physical GPU instances to provision across heterogeneous hardware under a global GPU budget constraint ($C_3$). CapOrches provides the profile-guided optimization intelligence that decides what to provision; Ray or Kubernetes acts as the downstream execution substrate ($R_8$)."*

### Challenge 4: "Is global re-optimization really practical at scale?"
* **Target Respondent:** Role 075 / Role 077
* **Defensible Answer:**
  > *"Yes, for two reasons:
  > 1. **Structural Coupling:** In Finding F18, we measured profile overlap across concurrent workflows and found 84% to 100% sharing. Furthermore, all workflows share the global GPU budget cap $B$ in $(C_3)$. Scoped sub-problem re-optimization is mathematically vacuous because changing instances in one workflow immediately perturbs the budget available to others.
  > 2. **Sub-Second Runtime:** Track C (`C+cons`) with memoized headroom vector caching solves a 64-task cluster in 13.8ms and a 128-task cluster in 106ms. Because global solving takes under a tenth of a second, scoped approximations are unnecessary."*

---

## 4. 60-Second Live Terminal Demonstration Protocol

During the meeting, run this exact sequence in PowerShell to demonstrate verification to Prof. Tossaphol:

```powershell
# Step 1: Run the automated T0 pre-flight verifier
python scripts/verify_t0_readiness.py

# Step 2: Run a quick 5-seed closed-loop drift simulation with ASCII timeline
python scripts/run_closed_loop_benchmark.py --seeds 5

# Step 3: Open the generated formal sign-off record and publication figures
cat docs/T0_Ratification_Signoff_Record.md
```

### Expected Terminal Verifier Output:
```
[Check 1] Verifying Mathematical Invariants (I1-I5)...       [PASS]
[Check 2] Verifying Aggregate Capacity Coupling (C2)...      [PASS]
[Check 3] Verifying Heterogeneous Price-GPU Decorrelation...  [PASS]
[Check 4] Verifying Lagrangian Duality Hierarchy...          [PASS]
[Check 5] Verifying Closed-Loop Drift Differentiation (F24).. [PASS]
ALL PRECONDITIONS SATISFIED. T0 RATIFICATION SESSION READY FOR SIGN-OFF.
```

---

## 5. Formal Ratification Sign-Off Checklist

Before concluding the session, ensure all checklist items are verified:
- [ ] Mathematical formulation in `docs/System_Architecture_v2.md` §1 confirmed unanimously.
- [ ] Option A (Hard SLA Floor Constraint) ratified over Option B by Prof. Tossaphol.
- [ ] Decision variables confirmed ($x$: Level 1 routing, $n$: Level 2 provisioning).
- [ ] Constraint $(C_2)$ acknowledged as the multi-workflow coupling bridge.
- [ ] Invariants $I_1–I_5$ confirmed as the non-negotiable correctness gates.
- [ ] Formal sign-off recorded in [`docs/T0_Ratification_Signoff_Record.md`](T0_Ratification_Signoff_Record.md).
