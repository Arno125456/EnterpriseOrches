# PoC Findings — running log

**Status: preliminary.** Recorded 2 September 2026, in Week 1 of the §5.4 schedule. These
are early readings from the harness, not the deliverables. D5/D6 are due 15 Sep, D9 22 Sep,
D10 26 Sep, and the consolidated report D11 on 29 Sep.

Nothing here has been reviewed by the team. Several items contradict assumptions in
`System_Architecture_v2.md`, which is the point of running the tests early — but a
contradiction found by one person on one afternoon is a prompt for discussion, not a
settled result.

## Reproducing these numbers

```bash
python -m poc.harness.runner        # or, in a REPL:
```

```python
from poc.harness.runner import sweep
from poc.harness import metrics
records = sweep(n_tasks=8, n_profiles=4,
                tightness_values=[0.5, 0.6, 0.7, 0.8, 0.9, 1.0], seeds=range(25))
print(metrics.format_table(metrics.summarise(records)))
print(metrics.solvability(records))
```

Everything below is 8 tasks, 4 profiles, seeds 0–24, six tightness levels — 150 instances,
64 of which the exact solver could solve.

### The full table

```
cond    inst  feas  infeas  =opt  mean gap%  max gap%  bound gap%   time s
--------------------------------------------------------------------------
MILP      64    64       0    64       0.00      0.00        0.00    0.032
STATIC    64    27      37     7      23.06     46.55           -    0.000
A         64    37      27    23      10.28     40.43           -    0.000
A+M1      64    47      17    29       9.39     40.43           -    0.000
B         64    59       5    55       0.93     16.96        2.40    0.954
C         64    37      27    16      14.58     70.49       15.21    0.029
C2        64    43      21    20      13.16     70.49       15.46    0.025
```

`infeas` counts instances the exact solver could solve but the condition could not. Read it
alongside `mean gap%`, which is over feasible runs only — a condition that solves just the
easy instances posts a flattering gap.

---

## F1 — T2 is confirmed on the fixture: greedy is defeated by aggregate coupling

`instances/fixtures/adversarial_3t2p.py`, hand-verified and now re-verified by exhaustive
enumeration in the test suite:

| Condition | Cost | Routing |
|---|---|---|
| Exact MILP | **280** | `t1→m2, t2→m2, t3→m1` |
| Track C | **280** | same |
| Track A (plain greedy) | **300** | everything on `m1` |

Greedy's myopia costs 20 (7.1%). The fixture also records, by enumeration, that neither
multi-start (all six orderings return 300) nor single-move relocate recovers it — the
improving move is `t1` and `t2` *together*.

**Consequence, per §5.3's T2 table:** the outcome is "greedy fails, relocate does not
recover", which is off the bottom of that table. It points at a multi-move neighbourhood
or a consolidation step, not at relocate. This is evidence for §3.1.7 needing a
sub-module it does not currently specify.

**Caveat.** One hand-built instance, constructed to defeat greedy. F4 is what happens on
instances not built for that purpose, and it does not agree.

---

## F2 — §6.4's budget anchor did not work, and T3 could not sweep against it [FIXED, SIGNED OFF]

§6.4 anchors the budget to "a naive one-instance-per-profile solution", `Σ_m gpu(m)`.
Implemented literally, then measured — solvable = the exact MILP found any allocation, out
of 25 seeds:

| tightness | 0.3 | 0.4 | 0.5 | 0.6 | 0.75 | 1.0 |
|---|---|---|---|---|---|---|
| solvable | 0 | 0 | 3 | 6 | 12 | 16 |

The anchor does not depend on the tasks at all, so 8 tasks routinely need more instances
than one-per-profile. The budget landed below feasibility nearly everywhere, and **T3's
primary axis had no room to move even at its loosest setting.**

The anchor is now a concrete, always-achievable reference allocation — every task to its
most GPU-efficient eligible profile, instance counts derived from routed load. Being a real
allocation rather than a bound, a budget equal to it always admits a solution:

| tightness | 0.4 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 | 1.0 |
|---|---|---|---|---|---|---|---|
| solvable | 0 | 1 | 3 | 6 | 13 | 16 | 25 |

`budget_tightness` keeps its §6.4 meaning — a fraction of an anchor — so the sweep reads
the same way. Only the anchor changed.

**Signed off 2 September 2026**, and §6.4 in `System_Architecture_v2.md` has been amended
to match, with the measurements that forced it. A separate wrinkle left alone: the parameter name runs backwards against its
value, since 1.0 is the *loosest* budget. That inversion is §6.4's.

---

## F3 — Both heuristics are infeasible on a third to a half of solvable instances

This is the largest problem currently visible, and it is not the one the plan expected to
be largest.

| tightness | solvable | A infeasible | C infeasible |
|---|---|---|---|
| 0.5 | 1 | 1 | 1 |
| 0.6 | 3 | 2 | 3 |
| 0.7 | 6 | 3 | 2 |
| 0.8 | 13 | 7 | 6 |
| 0.9 | 16 | 7 | 6 |
| 1.0 | 25 | **7** | **3** |

Track A fails 27 of 64, Track C 21 of 64. Note the last row: **both tracks fail at the
loosest budget the generator produces**, where a feasible allocation is guaranteed to exist
by construction.

17 of those failures are shared; 10 are Track A only and 4 are Track C only. So it is
mostly a property of the instances and of the shared decision rule, not of either track's
own logic.

**Why.** `select_profile` ranks on `admit.extra_cost` — price — and never looks at
`extra_gpus`. Both tracks therefore buy cheap-but-GPU-hungry profiles early, exhaust the
budget, and strand later tasks with no admissible option. The GPU-efficient allocation is
affordable the whole time; neither track aims at it. Track C inherits this because §5.2.1
gives its repair pass the same cost-only `costAdjust`.

**This is per spec, not a bug.** §5.2.1 defines Track A's `costAdjust` as `extraCost` and
Track C's repair identically. So the finding is about the shared decision rule, not the
implementation of it.

**The RATE is partly an artefact of the anchor, and should not be quoted.** F2 sets the
budget to the GPUs used by the *most GPU-efficient* allocation — that is, in terms of
exactly the quantity this finding says the tracks ignore. A track that does not optimise
GPU-efficiency is therefore pushed toward overshooting almost by construction. The
mechanism is real and independent of the generator; the 42% is not. Evidence that the
anchor is an amplifier rather than the whole story: at tightness 1.0, plain greedy fails on
28% rather than nearly all, and Track B — whose repair is equally cost-only — fails on just
1 of 25 (F11). Cost-blind ranking is a handicap, not a death sentence.

**Consequence, per §5.3's T4 table:** this is the third outcome — "greedy frequently
infeasible → the construction needs the M1 analogue (O2) before it is viable" — arriving
three weeks earlier than T4 was scheduled. Whatever the M1 analogue turns out to be, it has
to make the ranking budget-aware. **Deliberately not implemented**: that is the machinery
T4 exists to evaluate, and building it now would prejudge the test. 035's call.

---

## F4 — Preliminary T4 signal on A vs C *(superseded by F10)*

Over solvable instances, cost gap above the exact optimum, feasible runs only:

| tightness | A mean gap% | C mean gap% | LP bound gap% |
|---|---|---|---|
| 0.7 | 10.87 | 11.14 | 13.72 |
| 0.8 | 8.26 | 8.79 | 15.79 |
| 0.9 | 10.00 | 10.22 | 14.90 |
| 1.0 | 11.56 | 16.25 | 15.92 |

Head-to-head on the 33 instances where both produced a feasible answer:

| | count |
|---|---|
| Track A strictly cheaper | 7 |
| Track C strictly cheaper | 2 |
| tied | 24 |

**Plain greedy is not losing to LP-rounding — it is marginally ahead on cost.** On the
fixture built to defeat it, greedy loses by 7%; on instances not built for that purpose it
wins or ties 31 times out of 33.

Where Track C is clearly better is **feasibility**: it fails 21 times to Track A's 27, and
only 3 times at the loosest budget against Track A's 7.

**Consequence, per §5.3's T4 table:** the first outcome — "greedy within a few percent of
LP-rounding → the full AGH machinery likely does not pay; simplify or cut Track A". Note
what this does and does not say. It does not say greedy is good; both tracks sit 8–16%
above optimum and fail often. It says the *elaborate* Track A is hard to justify on cost
when the plain version already matches a solver call — while the solver call is the more
reliable of the two at actually returning an answer.

**Caveat, since resolved.** At the time of writing Track C got two realisation attempts to
Track A's one. That has been equalised — `C` is now single-shot and `C2` carries the extra
attempt as its own condition. **F10 is the current T4 picture**; this finding is kept for
the record of how it looked before Track B and A+M1 existed.

---

## F5 — The LP integrality gap is large, as §1.7 predicts

Mean gap between the LP bound and the true optimum: **~15%**, stable across tightness
(13.7 / 15.8 / 14.9 / 15.9).

§1.7 says the integrality gap lives in (C2), because `n[m]` must cover a ceiling of
aggregate load over throughput and the LP returns fractional instance counts. A 15% gap is
consistent with that and is worth stating in Ch.2: it is the room an integer-aware method
has to beat the LP.

**This is the number T1 cares about.** Track B earns its place only if its bound closes
some of that 15%. If Track B's bound lands at the LP bound, §5.3's T1 table fires its last
row and the track should be cut or rejustified. That test is now cheap to run — the harness
records `bound_gap` for any track that reports a bound.

---

## F6 — The LP returns an integral routing. O6 is largely a non-question.

O6 asks for "the LP rounding policy". Two alternative policies were built to answer it —
one restricting to profiles the LP had opened (`n[m] > 0`), one taking the most
GPU-efficient profile among those with LP weight. Both were **deleted**, because across 76
instances they produced routings byte-identical to plain argmax, every single time.

The reason is structural. Measured over 80 LP solutions at 8 tasks / 4 profiles:

| quantity | value |
|---|---|
| `x[t][m]` values integral (0 or 1) | **99.5%** |
| LP solutions with fully integral `x` | **96%** (77 of 80) |
| `n[m]` values fractional | 53.4% |

The LP has no reason to split a task. `n[m]` is continuous in the relaxation, so it can buy
exactly the capacity a whole task needs. **All the fractionality — and therefore the entire
integrality gap — sits in `n[m]`**, exactly where §1.7 predicts it.

**Consequence for 075:** effort spent designing a rounding policy for the routing is close
to wasted. What determines Track C's cost is the **repair pass** that runs when the LP's
integral routing stops fitting once `n[m]` must be a whole number and (C3) binds. That is
the piece worth designing, and O6 should probably be reworded to say so.

**What did help.** Realising each candidate routing in two task orders — large-first and
small-first — cut infeasibility from 27 of 64 to 21, and mean gap from 14.6% to 13.2%. The
entire gain came from the second *order*, not from any policy. That is also what creates
the fairness wrinkle noted in F4: Track C now gets two attempts, Track A one.


---

## F7 — T1: the Lagrangian bound is consistently tighter than the LP bound

**The bound result is clean. The cost and feasibility results are confounded — read both
halves of this finding.**

Track B was built relaxing **(C1)**, the assignment constraints, because that is what §1.8
predicts for capacitated facility location. That choice is *an assumption adopted so T1 had
something to measure*, not a result. Relaxing (C3) has not been implemented, so T1's
decomposition question is answered only in the sense that (C1) does decompose per profile,
as predicted. v1's per-workflow claim is contradicted either way.

### The bound — clean, and decisive for O3

The bound comes out of the relaxation. It does not touch the primal heuristic, so nothing
below contaminates it.

| | Track B | Track C |
|---|---|---|
| mean bound gap below the true optimum | **2.40%** | 15.21% |
| invalid bounds (above the optimum) | **0** | 0 |

*The 6× ratio here is the uniform generator's. On the structured generator it is 2.8×
(8.39% against 23.47%) — see F12. "Consistently tighter" is robust; the multiplier is not.*

Over a separate 30-instance check, the Lagrangian bound was **strictly tighter than the LP
bound on 30 of 30**, never looser, never equal. On the hand-verified fixture it reaches
**280 — the exact optimum** — against the LP's 190.8.

**Consequence, per §5.3's T1 table:** the row to watch was *"Lagrangian bound = LP bound
consistently → Track B provides nothing Track C does not; cut it or rejustify"*. **That row
does not fire.** On this evidence Track B earns its place and §5.2.3 stands.

Two implementation choices protect this number, and both err against Track B: (C3) is
dropped rather than relaxed, which weakens the bound but keeps it valid; and the knapsack
scales float loads in the permissive direction — weights down, capacity up — which can only
*understate* the bound. So the result is not an artefact of favourable rounding.

### The cost and feasibility — confound checked, and it does not bind

Track B's subgradient step rule takes its incumbent upper bound from plain greedy. That
looked disqualifying: it would mean Track B could never be worse than Track A and never
fail where Track A succeeded, by construction rather than by merit.

So the identical relaxation was re-run with the warm start disabled (`B-cold`). The two are
**identical on every column**:

| | B (warm) | B-cold |
|---|---|---|
| feasible, of 64 solvable | 59 | 59 |
| matched the exact optimum | 55 | 55 |
| mean gap | 0.93% | 0.93% |
| bound gap | 2.40% | 2.40% |

**The warm start is inert.** Track B's own primal repair independently finds solutions at
least as good as greedy's on every instance measured, so the confound does not bind and the
cost column may be quoted.

That "identical" is only meaningful if the flag changes what runs, so it is verified rather
than assumed: warm-started Track B calls greedy exactly once, `B-cold` calls it zero times
(`test_warm_start_flag_actually_takes_effect`). Both facts are locked in by tests — if the
warm start ever stops being inert, the T4 comparison becomes circular again and only the
`B-cold` row may be used.

Against plain Track A, independently:

| | count |
|---|---|
| B-cold fails where A succeeded | **0** |
| B-cold strictly cheaper (of 37 both-feasible) | **11** |
| A strictly cheaper | **0** |
| tied | 26 |

### The runtime, which is the real trade

Track B costs **~0.95 s per instance** against Track C's 29 ms and Track A's under a
millisecond — roughly 30× Track C at 8 tasks. The subproblem is an exact knapsack DP per
profile per iteration, up to 120 iterations. Irrelevant at PoC scale; the first thing to
break if instances grow, and precisely the trade T4 should be pricing.

**Other caveats.** Step-size schedule, tolerance and iteration cap (O5) are untuned
defaults, not fitted and not justified by experiment.

---

## F8 — The M1 lookahead works, and it is free

Decision 2 asked for the M1 analogue as a separate condition so T4 could price it rather
than assume it. Priced:

| | A (plain greedy) | A+M1 (feasibility lookahead) |
|---|---|---|
| infeasible, of 64 solvable | 27 | **17** |
| matched the exact optimum | 23 | **29** |
| mean gap | 10.28% | **9.39%** |
| runtime | <1 ms | <1 ms |

**A 37% reduction in failures, and it also got slightly cheaper, at no measurable runtime
cost** at this scale. The lookahead has no tuning parameter — it is a feasibility test, not
a re-weighting — so it cannot have been fitted to these instances.

It does not eliminate the failure mode: 17 instances still strand a task. The lookahead is
one step and checks each remaining task in isolation, so it cannot see that two of them
need the same last GPU.

**Consequence:** F3's diagnosis is confirmed by construction. The failures were caused by
the shared rule ignoring `extra_gpus`, and making the construction feasibility-aware fixes
a large share of them. **035 still needs to reconcile `track_a_m1.py` against Cheng &
Nguyen's real M1** — this is an analogue built from the observed failure, not their
algorithm.

The complexity price is asymptotic, not wall-clock: O(|T|²·|C|²) against plain greedy's
O(|T|·|C|). Invisible at 8 tasks; the thing to watch if instances grow.

---

## F9 — The no-optimisation baseline is much worse, which is the point

| | STATIC | best heuristic |
|---|---|---|
| infeasible, of 64 solvable | **37** | 5 (B) |
| matched the optimum | 7 | 55 (B) |
| mean gap | **23.06%** | 0.93% (B) |

STATIC routes every task to its cheapest eligible profile independently — no coupling
awareness, no budget awareness. It fails on 58% of solvable instances and sits 23% above
optimum when it does succeed.

This is the sanity check the evaluation needed: the optimisation is doing real work.
Without this row, "Track A is 10% above optimum" has no scale to be read against.


---

## F10 — T4, consolidated: Track B dominates, and the question has changed shape

All conditions, 64 solvable instances, ordered by mean gap:

| condition | infeasible | matched optimum | mean gap | runtime |
|---|---|---|---|---|
| MILP (exact / Murakkab) | 0 | 64 | 0.00% | 32 ms |
| **B** (Lagrangian) | **5** | **55** | **0.93%** | 954 ms |
| A+M1 (greedy + lookahead) | 17 | 29 | 9.39% | <1 ms |
| A (plain greedy) | 27 | 23 | 10.28% | <1 ms |
| C2 (LP + 2 attempts) | 21 | 20 | 13.16% | 25 ms |
| C (LP + rounding) | 27 | 16 | 14.58% | 29 ms |
| STATIC (no optimisation) | 37 | 7 | 23.06% | <1 ms |

### T4 as originally asked

*"Is Track A worth its cost relative to Track C? Track A has six sub-modules and produces
no bound; Track C is a solver call plus rounding."*

On equal terms — one attempt each — **plain greedy beats LP-rounding**: 10.28% against
14.58%, identical feasibility (27 failures each), and it does so roughly 30× faster. Give
Track C its second attempt (C2) and it closes to 13.16% with 21 failures, still behind on
cost while ahead on feasibility.

So the answer to T4 as written is **neither track earns much over the other**, and per
§5.3's first outcome the elaborate Track A machinery is hard to justify against Track C —
because the *plain* version already matches it.

### But that is no longer the interesting question

Track B is at **0.93% mean gap with 5 failures**, against every heuristic's 9–15% and 17–27
failures. It matches the exact optimum on 55 of 64 instances. Its bound gap is 2.40%
against Track C's 15.21%.

The real T4 trade is no longer A versus C. It is **Track B's quality against its runtime**:
954 ms per instance versus under a millisecond for greedy, at 8 tasks and 4 profiles. That
ratio is the thing to measure as instances grow, and it is not measured here — §5.7 stands,
nothing in this PoC says anything about scale.

### What the team should take from this

1. **A+M1 over plain A, on this evidence.** Same runtime, 37% fewer failures, lower gap.
2. **Track C is the weakest of the three tracks** on both cost and feasibility, and is only
   worth keeping for its bound — which Track B beats by 6×. Its own §5.9 status of "stable,
   least affected" is no longer the whole story.
3. **T4's decision criteria need rewriting** before D10. They ask an A-versus-C question
   that the data has moved past.


---

## F11 — The pooled table oversamples loose budgets. Broken out, the picture mostly holds.

The aggregate table in every finding above pools all tightness levels, and the sample is
badly skewed toward the loosest: of 64 solvable instances, **25 come from tightness 1.0 and
41 from the two loosest levels**. T3's whole premise is that the evaluation has signal only
where the budget binds, so a pooled mean is weighted toward the region the plan says shows
least. That is a defect in how the results were presented, not merely a caveat.

Broken out — `inf` = infeasible, `=opt` = matched the exact optimum:

```
 tight  solv |         A          |       A+M1         |         B          |         C
             | inf  gap%   =opt   | inf  gap%   =opt   | inf  gap%   =opt   | inf  gap%   =opt
   0.6     3 |   2   0.0      1   |   1   0.0      2   |   1   0.0      2   |   3     -      0
   0.7     6 |   3  10.9      2   |   3  10.9      2   |   1   0.0      5   |   3  14.9      1
   0.8    13 |   7   8.3      4   |   5   6.2      6   |   1   1.4     11   |   7  10.3      3
   0.9    16 |   7  10.0      6   |   5  10.9      6   |   1   1.1     14   |   8  10.0      4
   1.0    25 |   7  11.6     10   |   3  10.8     12   |   1   0.9     22   |   5  17.7      8
```

**Track B's dominance is not a pooling artefact.** It leads at every tightness level, and
its failure count is **exactly 1 at every level** — the same instance, regardless of how
many are solvable. Where the budget binds hardest (0.7–0.8), the separation is at its
widest: B is at 0.0–1.4% gap against A's 8.3–10.9% and C's 10.3–14.9%.

**Track C is worst where the budget binds.** At tightness 0.6 it fails on all three solvable
instances. Its `§5.9` billing as "stable, least affected" does not survive contact with the
binding region.

**A+M1's advantage narrows under pressure.** It halves failures at 1.0 (7→3) but barely
helps at 0.7 (3→3). The lookahead is one step, and one step is not enough when almost
nothing fits.

### What this does and does not rescue

It answers the sampling objection. It does **not** answer the scale objection, and the two
are easy to confuse. Every row here is 8 tasks and 4 profiles.

Note what Track B actually is at this size: its subproblem is an exact knapsack, and at 8
tasks that knapsack is trivial to solve exactly. So Track B is close to an exact method
wearing a heuristic's clothes. The plausible failure mode is not that it is wrong, but that
**everything making it good here is what scale erodes** — knapsack DP cost, iteration count,
and the duality gap all grow together. Until that is measured, "Track B dominates" is a
claim about 8-task instances and nothing more.


---

## F12 — Re-run on a second, structurally different generator: most findings survive

The standing objection to everything above was that it all came from one generator written
by the same hand as the tracks and the metrics. `instances/structured_generator.py` was
built to disagree wherever it plausibly could — sublinear throughput against linear price
(so large profiles are bad value per GPU, inverting the original's near-neutrality),
lognormal loads instead of uniform, GPU tiers {1,2,4,8}, floors clustered on a minority of
tasks. Measured difference: loads 7× more heavy-tailed, pool sizes skewed the opposite way.

Same conditions, same harness, same anchor. 8 tasks, 4 profiles, seeds 0–24, tightness
0.6–1.0.

```
                UNIFORM (63 solvable)          STRUCTURED (75 solvable)
cond      infeas  =opt   gap%   bound%   infeas  =opt   gap%   bound%
STATIC        36     7  23.06        -       44     7  25.48        -
A             26    23  10.28        -       29    23  14.78        -
A+M1          17    28   9.59        -        2    42  11.34        -
B              5    54   0.95     2.44        1    65   1.76     8.39
C             26    16  14.58    15.21       22    18  18.69    23.47
```

Zero invariant violations on either generator.

### What survived

**Track B's dominance (F10/F11).** 1 infeasible of 75, 65 exact optima, 1.76% mean gap. It
still beats every heuristic on both cost and feasibility, on instances built to be
structurally hostile to the first generator's assumptions. This is the strongest evidence
in the whole log, and it is the finding I most expected to break.

**The Lagrangian bound beats the LP bound (F7).** Still true everywhere — but see the
correction below.

**STATIC is much worse (F9).** 25.48% gap, 44 of 75 infeasible. Optimisation is doing real
work under both structures.

**Neither A nor C clearly wins (F4).** Greedy is cheaper (14.78% vs 18.69%), Track C is more
often feasible (22 failures vs 29). The same inconclusive split as before, for the same
reason: they are differently bad rather than one being better.

### The correction: "6× tighter" was a generator-specific number

F7's headline said the Lagrangian bound is **6× tighter** than the LP bound. That is the
uniform generator's number (2.44% against 15.21%). On the structured generator the ratio is
**2.8×** (8.39% against 23.47%).

Both bounds loosen on the harder instances, and Track B's loosens proportionally more. The
robust claim is **"consistently tighter, by a factor between roughly 3 and 6 depending on
instance structure"** — not "6×". T1's conclusion is unaffected: the "cut Track B" outcome
still does not fire, because the bounds never converge. But the multiplier should not be
quoted without the qualifier, and I had quoted it.

### The upgrade: A+M1 is far more valuable than the first generator suggested

| | uniform | structured |
|---|---|---|
| infeasible, A → A+M1 | 26 → 17 (−35%) | **29 → 2 (−93%)** |
| exact optima, A → A+M1 | 23 → 28 | **23 → 42** |

On instances with heavy-tailed loads and expensive large profiles, feasibility is far more
fragile — and the lookahead is worth much more. This also **overturns F11's caveat** that
A+M1's advantage narrows under pressure; that was a property of the uniform generator, not
of the mechanism. Still no measurable runtime cost.

### One thing that got worse, and is worth watching

Track C's **maximum** gap on structured instances is **100.85%** — a solution costing twice
the optimum. Its mean is 18.69%, so this is a tail, not typical. But a track whose worst
case is 2× optimum is not one to put in front of an advisor without knowing why. The
suspect is the repair pass under a heavy-tailed load: one very large task lands badly and
drags a whole large instance open. Not diagnosed.

### What this still does not answer

The scale objection, untouched. Both generators run at 8 tasks and 4 profiles. Note that
the exact MILP's runtime already **doubled** on the structured instances (37 ms → 80 ms)
while Track B's fell slightly — the first hint that instance structure, not just size,
drives the solver cost that the whole heuristic premise depends on.


---

## F13 — Scale: the exact solver does break down, and Track B breaks down faster

This is the finding that changes the project's conclusions, and it goes against the track
the rest of this log has been praising.

### Does the exact MILP break down at all?

Objective 1.2.2 asks for *"non-exact alternatives to MILP"*. That premise requires the MILP
to become expensive somewhere. It does — but far later than expected, and only on one
instance family. Mean over 3 seeds, tightness 1.0:

| tasks / profiles | uniform | structured |
|---|---|---|
| 8 / 4 | 0.022 s | 0.058 s |
| 16 / 6 | 0.115 s | 0.170 s |
| 32 / 8 | 0.266 s | 0.256 s |
| 64 / 10 | 1.400 s | 0.300 s |
| **128 / 12** | **21.2 s** (max 55 s) | **1.9 s** |

**Instance structure matters more than instance size.** The uniform generator's profiles are
near-interchangeable, which gives CBC a large symmetric search space; the structured
generator's distinct GPU tiers and heavy-tailed loads break that symmetry and stay cheap.
Note this *reverses* with scale — structured instances were the harder ones at 8 tasks
(58 ms against 22 ms) and are 11× cheaper at 128.

**Consequence:** the premise holds, but only for a specific instance family, and "MILP is
too slow" cannot be asserted without saying on what. Any Chapter 3 claim needs to name the
family.

### Does Track B scale into the gap?

No. It is the opposite of what the 8-task results implied. Uniform generator, 2 seeds:

| tasks | MILP | Track B | B ÷ MILP | B gap |
|---|---|---|---|---|
| 8 | 0.031 s | 0.69 s | 22× | 0.00% |
| 16 | 0.053 s | 7.52 s | 142× | 1.51% |
| 24 | 0.115 s | 15.05 s | 131× | 0.00% |
| 32 | 0.321 s | **34.55 s** | **108×** | 0.04% |

**Track B is roughly 100× slower than the exact method it exists to replace, at every size
tested.** Its answers are excellent — 0–1.5% gap — but you would always have been better off
running the MILP, which is both faster and optimal. A heuristic that is slower than exact
has no reason to exist as a heuristic.

This is exactly the failure predicted when Track B's dominance was first questioned: its
subproblem is an exact knapsack, which is cheap at 8 tasks and is precisely what scale
erodes. Extrapolating its growth, Track B would need hundreds of seconds where the MILP
needs 21.

### The caveat that matters, and it is not small

**This may be my implementation rather than the method.** The subproblem is a pure-Python
0/1 knapsack DP with a full traceback table, O(n × capacity) per profile per iteration, run
for up to 120 iterations, with capacity scaled by 100. That is the obvious suspect, and a
vectorised DP, a coarser scale, a smarter iteration schedule, or early termination could all
move it by an order of magnitude or more.

What is *not* implementation-dependent is the shape: capacity grows with total load, so the
subproblem cost grows with the batch, and it is paid per profile per iteration. Lagrangian
relaxation here is inherently heavy. Whether it is 100× heavy or 10× heavy is an open
engineering question. **075 should not read this as "Track B is dead" — it should read as
"Track B's subproblem needs profiling before any scale claim is made."**

### What this does to T4

The T4 answer at 8 tasks and the T4 answer at 32 tasks are different answers.

At 8 tasks (F10): Track B dominates on quality, everything else is 9–18% above optimum.

At 32 tasks: the MILP solves in 0.32 s and is optimal. Track B takes 34 s to be 0.04% worse.
**Track C stays fast** — 0.092 s at 32 tasks — and its gap *improves* with scale (11.3% → 3.8%),
as does A+M1's (11.3% → 5.1%).

So the practical ordering inverts. Track B's value is not as an allocator but as a **bound
generator**, which is what §5.2.3 always said it was for and what T1 measures. Its cost as
an allocator is not competitive at any size measured.

### What is still not known

Where the crossover is. Track B was not run past 32 tasks because it takes 34 s per
instance there; the MILP does not become genuinely expensive until ~128 on uniform
instances. Whether a *profiled* Track B could win in that window is the open question, and
it is an engineering question, not a research one.


---

## F14 — At scale the ordering inverts: Track C wins, the greedy tracks collapse

5 seeds per row, tightness 1.0. `inf` counts instances the MILP solved and the condition
could not. Track B is absent past 32 tasks — at 34 s per instance it was not runnable here,
which is itself F13's finding.

**uniform**

| tasks/prof | MILP s | C s | C gap | C inf | A gap | A inf | A+M1 gap | M inf |
|---|---|---|---|---|---|---|---|---|
| 16 / 6 | 0.125 | 0.056 | 8.15% | 1 | 9.49% | 1 | 9.49% | 1 |
| 32 / 8 | 0.222 | 0.106 | 3.90% | 1 | 7.27% | 2 | 7.23% | 1 |
| 64 / 10 | 11.288 | 0.114 | **0.53%** | 3 | — | **5** | — | **5** |
| 128 / 12 | 10.997 | 0.110 | **1.16%** | 3 | — | **5** | — | **5** |

**structured**

| tasks/prof | MILP s | C s | C gap | C inf | A gap | A inf | A+M1 gap | M inf |
|---|---|---|---|---|---|---|---|---|
| 16 / 6 | 0.194 | 0.102 | 22.53% | **0** | 8.31% | 4 | 4.15% | 3 |
| 32 / 8 | 0.281 | 0.119 | 8.28% | **0** | — | 5 | — | 5 |
| 64 / 10 | 0.215 | 0.124 | 6.98% | 1 | — | 5 | — | 4 |
| 128 / 12 | 1.365 | 0.228 | **2.86%** | **0** | — | 5 | — | 5 |

### Track C is the only heuristic that works at scale

Its gap **improves monotonically** with size on both generators — 8.15% → 1.16% on uniform,
22.53% → 2.86% on structured — while its runtime stays essentially flat, 0.06 s to 0.23 s
across a 16× increase in tasks.

At 64–128 tasks on uniform instances that is a **~100× speedup over the exact solver for
roughly 1% cost** (11 s → 0.11 s). That is exactly what Objective 1.2.2 asks a non-exact
alternative to deliver, and it is the first result in this log that delivers it.

The likely reason the gap shrinks: the integrality gap is a *rounding* penalty, and rounding
error amortises over more tasks. With 8 tasks one badly-rounded profile is a large fraction
of total cost; with 128 it is not.

### The greedy tracks fail here — but see F15 before believing why

Track A fails on **all 5 instances** at 64 and 128 tasks on uniform, and from 32 tasks
upward on structured. A+M1 delays it but does not prevent it.

**This is largely an artefact of the budget anchor and is corrected in F15.** The tracks
recover completely — 0 of 5 to 5 of 5 — with 25% more budget. Do not quote "the greedy
tracks collapse at scale" from this section.

### I have to withdraw a correction I made

Two commits ago I amended §5.9 of the PoC plan to say Track C was **"contradicted by
measurement — weakest of the three tracks"**, on the strength of the 8-task results. That
was wrong, and it was wrong in the most instructive way: it was a confident conclusion drawn
from the only regime that had been measured.

At scale Track C is the **strongest** heuristic — the only one that returns answers at all
past 32 tasks, at ~1–3% of optimum and near-constant runtime. §5.9 has been amended again,
and this time it names the regime.

### What T4's answer actually is

| regime | best heuristic | why |
|---|---|---|
| ≤ 8 tasks | Track B on quality | 0.9% gap — but the MILP is 32 ms and optimal, so no heuristic is needed |
| 16–32 tasks | Track C | greedy is failing, B costs 100× the MILP |
| 64+ tasks | **Track C, decisively** | greedy returns nothing; MILP costs 100× more for ~1% |

**No heuristic is justified below ~32 tasks** — the MILP is faster and optimal. Above it,
exactly one of the three tracks earns its place, and it is not the one the 8-task data
favoured.


---

## F15 — F14's collapse was a knife edge, not a scaling failure. Correcting my own finding.

F14 reported that Track A and A+M1 fail on every instance at 64 and 128 tasks and concluded
that greedy construction collapses at scale. That conclusion is wrong, and the way it is
wrong is the same trap flagged against F3.

Every scale row was run at `budget_tightness = 1.0` — meaning the budget is set to **exactly**
the GPUs used by the reference allocation, which is the *most GPU-efficient* routing. That
is a razor-thin margin: any method that does not reproduce the GPU-efficient routing almost
exactly will overshoot. And the chance of a cost-ranking method matching it by accident goes
to zero as tasks are added. So the anchor manufactures a failure that grows with instance
size, and it is easy to mistake for a scaling property.

Feasible out of 5, as the budget is loosened past the reference:

| tasks | ×1.00 | ×1.25 | ×1.50 | ×2.00 | ×3.00 |
|---|---|---|---|---|---|
| 64 — Track A | **0** | **5** | 5 | 5 | 5 |
| 64 — A+M1 | **0** | **5** | 5 | 5 | 5 |
| 64 — Track C | 2 | 5 | 5 | 5 | 5 |
| 128 — Track A | **0** | **5** | 5 | 5 | 5 |
| 128 — A+M1 | **0** | **5** | 5 | 5 | 5 |
| 128 — Track C | 2 | 5 | 5 | 5 | 5 |

**A 25% budget increase takes every track from near-total failure to complete success.** The
cliff is entirely at the anchor point. Track C is less exposed — it gets 2 of 5 where greedy
gets 0 — because the LP naturally lands near a GPU-efficient solution, but even it is mostly
failing at ×1.00.

### What survives from F14, and what does not

**Does not survive:** "the greedy tracks collapse at scale". They fail at one specific budget
that the generator happens to make the default, and recover fully just past it.

**Survives:** Track C's cost gap improving with size (8.15% → 1.16% uniform, 22.53% → 2.86%
structured), its near-flat runtime, and the MILP's blow-up on uniform instances at 128
tasks. Those are quality and runtime results, not feasibility results, and the anchor does
not drive them.

**Also survives, and is strengthened:** F13's finding on Track B. Its 100× runtime penalty
is a timing measurement, untouched by feasibility.

### The methodological lesson, since it has now happened three times

`budget_tightness = 1.0` is not a neutral default. It is the tightest budget at which
feasibility is still guaranteed, which makes it the single most adversarial setting in the
sweep — and it is the one every scale run used because it is the only one where instances
are reliably solvable at size.

Anything measured only at ×1.00 is measured on a cliff edge. **T3's sweep should extend
above the reference, not just below it.** That is a change to the experimental design, and
it belongs to 089.


---

## What these findings do not establish

Restating §5.7, because early numbers invite over-reading:

- **Nothing about real workloads.** All instances are synthetic, from one generator whose
  distributions were chosen by hand.
- **Little at scale.** Findings F1–F12 are all 8 tasks and 4 profiles. F13 probes up to 128
  tasks and reverses the T4 conclusion, so every comparison above should be read as
  small-instance behaviour unless F13 says otherwise.
- **Nothing about which constraint Track B *should* relax.** It relaxes (C1) by assumption
  (F7). The (C3) alternative is unbuilt and unmeasured, so T1 is half-answered at best.
- **Nothing statistical.** 25 seeds per point, no confidence intervals, no significance
  testing. The head-to-head margins in F4 are tendencies, not results.
- **Two generators now, but both chosen by one author.** F12 re-ran everything on
  deliberately different structure and most findings held. That answers the sharpest form
  of the objection but not all of it: the same hand still wrote both, plus the anchor, the
  tracks and the metrics. Real workload data remains the only full answer, and it is out of
  PoC scope by §5.1.
- **Nothing about drift, execution, or the domain.** Out of PoC scope entirely.

No statement of the form "our approach reduces cost by X%" is supported by any of this.

---

## Decisions taken, 2 September 2026

All seven were answered in one pass. Recorded here with what was built as a result.

| # | Decision | Answer | Built |
|---|---|---|---|
| 1 | F2 anchor change | **Accepted** | §6.4 amended in `System_Architecture_v2.md` |
| 2 | The M1 analogue | **Build it, as a separate condition** | `tracks/track_a_m1.py`, condition `A+M1`. Plain Track A untouched, so T4 prices the machinery instead of assuming it |
| 3 | Which constraint Track B relaxes | **(C1), per §1.8's prediction** | `tracks/track_b_lagr.py`. Flagged in-module as an assumption, not a finding — see F7 |
| 4 | Reword O6 | **Done** | O6 now points at the repair pass, per F6 |
| 5 | Attempt parity | **Equalise, report the variant separately** | `C` is single-shot like `A`; `C2` carries the extra realisation order as its own row |
| 6 | O1, per-invocation cost term | **Closed: no** | Provisioning cost only. `ProfileSpec` has no `varcost` field |
| 7 | The STATIC baseline | **Build no-optimisation; Murakkab is not separate** | `tracks/static_baseline.py`. See the note below |

### On the Murakkab condition

The instruction was to build both a Murakkab baseline and a no-optimisation baseline. Only
one of those is a distinct thing to build.

Per §9's reference map, what this project takes from Murakkab is the capacity model and the
MILP baseline, and the formulation in §1 **is** Murakkab's model. So §4.7's own requirement
— "re-run Murakkab under matched conditions" — is satisfied by running `exact_milp`.
Registering a second condition that calls the same solver would print the same number twice
and imply an independent comparison that does not exist.

`MURAKKAB` is therefore listed in the harness's `UNAVAILABLE` map with that reasoning
attached, so anyone asking for it gets the explanation rather than silence.

**If the team means something narrower** — Murakkab's own published heuristic rather than
its exact solve — that is a genuinely different condition, and specifying it needs the
paper open. Flagging it rather than guessing.

---

## Still open

| # | Item | Owner |
|---|---|---|
| O5 | Track B's step-size schedule, tolerance, iteration cap — current values are untuned | 075 |
| — | Relaxing (C3) instead of (C1), so T1's decomposition question is actually tested | 075 |
| — | Rewrite T4's decision criteria: they ask an A-vs-C question the data has moved past (F10) | 089 |
| — | Track B's runtime as instances grow — the only trade that still matters for T4 (F10) | 089 |
| — | Reconcile `track_a_m1.py` against Cheng & Nguyen's real M1 | 035 |
| — | Whether Murakkab's published heuristic is a separate condition (see above) | Advisor |
| O8 | Is Track A worth its complexity? T4 proper, once the conditions above settle | 035 + 089 |
