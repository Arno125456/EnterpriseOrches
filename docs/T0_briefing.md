# T0 briefing — read before the session

**Deliverable D1, due 8 September.** The PoC plan calls this *"the single highest-risk item
in the plan"*: if the team cannot agree the formulation in one week, the PoC does not happen
on time.

**This session is a confirm-or-object exercise, not an open design debate.** Every item below
has a recommended default. If nobody objects, the default stands and the session is short.
That is the intended outcome.

You do not need to read the findings log first. Everything you need is on this page.

---

## Part 1 — The formulation (15 minutes)

The exit criterion from the plan is specific:

> Every member can state, unprompted, what `x` and `n` mean and which constraint couples
> workflows.

### In plain terms

We take a batch of workflows, all at once, before anything runs. We make **two** decisions:

- **`x[t][m]` — routing.** Which model profile serves task `t`. One profile per task.
- **`n[m]` — provisioning.** How many instances of profile `m` we pay for.

We minimise the total bill: `Σ n[m] × price(m)`. We do **not** pay per call — that was O1,
and it is closed as "no".

Three rules constrain us:

| | rule | in words |
|---|---|---|
| **C1** | `Σ x[t][m] = 1` | every task goes to exactly one profile |
| **C2** | `Σ load ≤ n[m] × thr(m)` | the instances we bought must handle the traffic we sent |
| **C3** | `Σ n[m] × gpu(m) ≤ B` | we cannot exceed the GPU budget |

**Reliability and latency are not in this list.** They are applied earlier, when we build
each task's candidate list `C(t)`. A profile that fails a task's floor is never considered.
That is deliberate — feasibility first, cost second.

### The three questions to be able to answer

1. **What is `x`?** Which profile serves each task.
2. **What is `n`?** How many instances of each profile we provision. Note it is *derived* —
   `n[m]` is the ceiling of the load routed to `m` divided by its throughput. It is not a
   free choice.
3. **Which constraint couples workflows?** **C2.** Two tasks in *different* workflows affect
   each other **only if they route to the same profile** — then they share its instances.
   That is the entire multi-workflow interaction. C1 and C3 do not couple workflows to each
   other.

If everyone can say those three things, T0 is met.

---

## Part 2 — Ask the advisor BEFORE the session

**One question, and it is the only thing that could invalidate the formulation.**

> Does "improve reliability" in the project brief mean (a) never go below a reliability
> floor, or (b) maximise reliability?

- If **(a) a floor** — everything above stands. This is what we assume.
- If **(b) maximise** — the objective becomes multi-objective, `§1.9` is wrong, and T0 would
  be ratifying a formulation we already know is out of date.

Do not run the session without this answer.

---

## Part 3 — Five decisions, each with a default (30 minutes)

Measurement during the PoC contradicted the documents in five places. Each is written as
*confirm or object*.

| # | Decision | Recommended default | If you object |
|---|---|---|---|
| 1 | **Is `§1` unchanged?** | **Unchanged.** Nothing measured contradicts C1/C2/C3 or the objective | Say exactly what changes — a change to C2 or the objective invalidates most results |
| 2 | **Budget anchor.** `§6.4` set the budget from a "one instance per profile" solution. Measured, that made 0–16 of 25 instances solvable and the T3 sweep had no room. It now uses a reference allocation instead | **Accept the change.** `§6.4` already amended | T3 needs a different experimental axis |
| 3 | **Track A.** Plain greedy sits 8–15% above optimum and gets worse with scale; Track C beats it at every size | **Cut Track A as a track**, but move its feasibility lookahead into the shared decision rule where every track benefits | Keep it, and T4's write-up must justify why |
| 4 | **Track B.** Best lower bound we have — paired, it sits 12.6 percentage points [9.5, 15.6] closer to the optimum than the LP bound — but ~100× slower than the exact solver as an allocator | **Keep it as a bound generator, not an allocator** | Someone must optimise its subproblem before any speed claim |
| 5 | **Scoped re-optimisation.** `§3.3` proposed re-optimising "affected workflows only". Measured, a drifted profile is used by 84–100% of workflows, so the affected set is nearly everything | **Drop scoping. Re-optimise globally** | Define what "scoped" should mean instead |

---

## Part 4 — Ownership sign-off (15 minutes)

Five design decisions were made during the PoC that belong to specific members. They are
already implemented. **Each needs its owner to say "yes, that's what I'd have done" or "no,
change it."**

This matters because at the viva, the person presenting has to defend it.

| Decision | Owner | What was done |
|---|---|---|
| The M1 analogue | **035** | A feasibility lookahead — check every remaining task still has an option before committing. It is *not* Cheng & Nguyen's actual M1, which is not specified in our documents |
| Consolidation neighbourhood | **035 / 075** | Move *all* tasks off one profile together. Fixes a rare, severe failure mode in Track C (median improvement is 0; the mean is tail-carried). Does not fix the adversarial fixture, which needs a *subset* move |
| Reliability estimator | **077** | `§4.5` says "EMA per observation". For reliability that reports 0.70 after 99 successes and one failure, and that number filters `C(t)`. Replaced with a counting estimator |
| Compatibility score | **077** | Invented, marked `[PROPOSED]`. Hatherley (2025) is not in the repo |
| Budget anchor | **083** | See decision 2 above |

---

## Part 5 — What to write down

The only output needed. Five lines and five names.

```
T0 session, __ September 2026.  Present: ______________________

Advisor's answer on O10 (reliability):  floor / maximise / not yet asked

1. Section 1 formulation:      unchanged / changed as follows: ____________
2. Budget anchor:              accepted / rejected
3. Track A:                    cut / kept
4. Track B:                    bound only / also an allocator
5. Scoped re-optimisation:     dropped / kept, defined as: ______________

Ownership accepted:
  M1 analogue ............ 035  yes / change: ______________
  Consolidation .......... 035/075  yes / change: ______________
  Reliability estimator .. 077  yes / change: ______________
  Compatibility score .... 077  yes / change: ______________
  Budget anchor .......... 083  yes / change: ______________

Disagreements recorded rather than resolved:
  ____________________________________________
```

The plan says explicitly: **record disagreements rather than resolving them silently.** An
unresolved disagreement written down is a success; an unnoticed one is not.

---

## If the session runs short of time

Do Part 1 and Part 2. Those are T0. Parts 3 and 4 are useful but can happen in the following
week without putting 30 September at risk.

If Part 1 cannot be agreed in one session, the plan is explicit: **escalate to the advisor
immediately, do not absorb it quietly.**
