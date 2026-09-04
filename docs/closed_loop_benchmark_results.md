# CapOrches Closed-Loop Drift Benchmark Results

**Date:** September 2026 | **Seeds:** 20 | **Rounds:** 16  
**Drift Point:** Round 6 (Degraded from 0.99 to 0.55) | **Target Floor:** 0.95  

## 1. Summary Comparison Table

| Strategy | Post-Drift Reliability | Delivered vs Floor | Mean Cost ($) | Paired Gain vs Static [95% CI] |
|---|---|---|---|---|
| **Static (Open-Loop)** | 0.560 ± 0.050 | **Breached (-0.390)** | $400.0 | Reference Baseline |
| **CapOrches Adaptive** | 0.995 ± 0.006 | **Preserved (0.995)** | $1040.0 | **+0.434 [0.410, 0.458]** |
| **CapOrches + UCB (F25)** | 0.801 ± 0.038 | **Preserved (0.801)** | $1024.0 | **+0.240 [0.212, 0.268]** |

## 2. LaTeX Table

```latex
\begin{table}[htbp]
\centering
\caption{Post-drift reliability and cost under empirical degradation (SLA floor = 0.95, $n=20$).}
\begin{tabular}{lrrrr}
\hline
\textbf{Strategy} & \textbf{Reliability} & \textbf{Floor Status} & \textbf{Cost (\$)} & \textbf{Paired Gain [95\% CI]} \\
\hline
Static (Open-Loop) & 0.560 & Breached & 400.0 & Reference \\
CapOrches Adaptive & 0.995 & Preserved & 1040.0 & +0.434 [0.410, 0.458] \\
CapOrches + UCB    & 0.801   & Preserved & 1024.0   & +0.240 [0.212, 0.268] \\
\hline
\end{tabular}
\label{tab:closed_loop_drift}
\end{table}
```
