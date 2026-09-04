# Heterogeneous Fleet 20-Seed Statistical Benchmark Results

**Date:** September 2026 | **Tasks:** 32 | **Profiles:** 8 | **Seeds:** 20  
**Budget:** 1.25× Reference | **Hardware Tiers:** Commodity (T4), Standard (A100), Premium (H100)

## 1. Summary Performance Table with 95% Confidence Intervals

| Strategy | Feasible | Opt Match | Mean Gap (%) [95% CI] | Max Gap (%) | Mean Bound Gap (%) | Mean Time (s) |
|---|---|---|---|---|---|---|
| **MILP** | 20/20 | 20 | 0.00% [0.00, 0.00] | 0.00% | - | 0.1775s |
| **B** | 15/20 | 5 | 1.34% [0.03, 2.64] | 8.50% | 2.00% [0.90, 3.11] | 0.4964s |
| **C+cons** | 15/20 | 3 | 5.69% [2.63, 8.74] | 16.01% | 2.80% [1.72, 3.87] | 0.0473s |
| **B-C3** | 16/20 | 4 | 5.20% [2.27, 8.14] | 16.01% | 2.77% [1.78, 3.76] | 0.0034s |
| **A+subset** | 3/20 | 0 | 4.39% [-2.38, 11.15] | 10.73% | - | 0.0039s |
| **A** | 1/20 | 0 | 18.33% | 18.33% | - | 0.0003s |

---

## 2. Active GPU Budget Trade-Off (Findings F31 & F32)

Under heterogeneous pricing, relaxing the GPU budget from $0.90\times$ to $1.50\times B_{\text{ref}}$ allows the solver to shift load from expensive premium instances to commodity instances:

* **Paired Dollar Savings:** **$180.16 [52.57, 307.74]** (95% CI, $n=8$)
* **Paired Percentage Savings:** **4.90% [1.69, 8.12]**
* **Budget Constraint Coupling:** Constraint $(C_3)$ actively shapes dollar cost in **100% of tested seeds** with zero inertness.

---

## 3. LaTeX Table for Proposal Chapters

```latex
\begin{table}[htbp]
\centering
\caption{Statistical benchmark on Heterogeneous Fleet (32 tasks, $n=20$ seeds, 95\% CI).}
\begin{tabular}{lrrrrr}
\hline
\textbf{Strategy} & \textbf{Feasible} & \textbf{Opt. Match} & \textbf{Mean Gap (\%)} & \textbf{Dual Bound Gap (\%)} & \textbf{Time (s)} \\
\hline
MILP       & 20/20    & 20    & 0.00% [0.00, 0.00]     & -                      & 0.1775s \\
B          & 15/20    & 5     & 1.34% [0.03, 2.64]     & 2.00% [0.90, 3.11]     & 0.4964s \\
C+cons     & 15/20    & 3     & 5.69% [2.63, 8.74]     & 2.80% [1.72, 3.87]     & 0.0473s \\
B-C3       & 16/20    & 4     & 5.20% [2.27, 8.14]     & 2.77% [1.78, 3.76]     & 0.0034s \\
A+subset   & 3/20     & 0     & 4.39% [-2.38, 11.15]   & -                      & 0.0039s \\
A          & 1/20     & 0     & 18.33%                 & -                      & 0.0003s \\
\hline
\end{tabular}
\label{tab:hetero_20seed_benchmark}
\end{table}
```
