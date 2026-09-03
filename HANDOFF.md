# Handoff — turning this work into the proposal

**Written 3 September 2026, at the end of a long working session.** The next session's job is
to make everything here the **core of the proposal** — not just T0, but Chapters 1 through 4,
the novelty argument, and the M1 presentation.

**If you want the ordered sequence rather than the reference material, read
[`PLAN.md`](PLAN.md) instead — eight steps, in order, ending at the presentation.** This
document is the detail behind those steps.

---

## 1. Where things stand in one paragraph

The proof-of-concept is complete: all four tests answered against the plan's *methods*, not
just its deliverables. 586 tests pass, reproducible from a clean clone. The optimizer works
and Track C is the result. Beyond the PoC, the closed loop was built and run end to end, and
it produced the project's strongest claim. Twenty-seven findings are recorded, of which
several correct earlier ones — **the corrections are as important as the results, and three
headline numbers were retracted after a statistical audit.**

Two branches are live and have diverged. **Read `BRANCHES.md` before merging anything.**

---

## 2. What the proposal needs, and what exists for each part

### Chapter 1 — problem and objectives

**Have.** The formalisation in `System_Architecture_v2.md` §1, and the plain-language version
in `docs/T0_briefing.md` Part 1. Objectives 1.2.1–1.2.4 are stated and three of the four now
have evidence.

**Missing.** The problem statement still reads as an optimizer project. It should lead with
the loop — see `docs/proposal_narrative.md` §1.

### Chapter 2 — literature

**Have.** `docs/research_papers/` tracks the papers. §1.8 identifies the problem as modular
capacitated facility location, which gives a citable literature beyond the two LLM-serving
papers. §9 is the reference map. The `mickie` branch adds P12 (DSPy).

**Missing, and it is the big one.** **O12 — the novelty argument — is unresolved.** §1.8
concedes the allocation problem is textbook, so novelty cannot be claimed there.
`docs/proposal_narrative.md` §4 sets out the defensible position: neither Murakkab nor Cheng
& Nguyen closes the loop. **That framing needs the advisor's agreement before it is written
up.**

### Chapter 3 — design and methodology

**Have, and this is the strongest chapter.** The formulation, the three tracks, the harness,
and 27 findings. `docs/D11_poc_report.md` is written for the advisor and is the natural
skeleton. `docs/proposal_narrative.md` §6 proposes the section order — deliberately putting
the optimizer *inside* the contribution rather than as the contribution.

**Missing.** Nothing structural. The work is to write it, and to make sure every number
quoted survives §5 below.

### Chapter 4 — evaluation plan

**Have.** A working harness with matched conditions and bias guards, two generators, and a
measured operating region (T3: 0.8×–1.25× the reference).

**Known defects, both flagged, neither fixed.** T4's decision criteria ask an A-vs-C question
the data has moved past. And **O13 is open** — whether `price(m)` is independent of `gpu(m)`.
Both generators tie them together, so the GPU budget does not change the optimal cost in 40
of 41 instances. Until O13 is settled, T3's region and T1's arm comparison are provisional.

### The Semester 2 story

R7 (monitoring), R8 (execution-time reliability) and R9 (framework integration) have **no
implementation** and are marked Absent in §8's traceability table. They come from the
advisor's brief, so the proposal must address them as planned scope rather than omit them.
`prototype/` is the honest answer for R4/R5: the loop exists and runs.

---

## 3. The claims the proposal can lead with

Ordered by how well they survive scrutiny.

| claim | evidence | strength |
|---|---|---|
| A static allocator silently violates its reliability floors under drift; the adaptive loop does not | paired **+0.424 [0.405, 0.442]**, n=20 | **Strongest in the project.** Mean equals median, tight interval |
| Filtering eligibility on a point estimate costs ~40% permanently; an upper confidence bound recovers the optimum exactly | paired saving **128 [74, 182]**, fixed condition has zero variance | Very strong |
| Track C returns within ~3% of optimal at 128 tasks with bounded, predictable runtime | 0.106 ±0.020 s vs the solver's 12.3 ±10.3 s | Strong — **argue predictability, not speed** |
| Greedy is defeated by aggregate coupling; neither multi-start nor relocate recovers it | hand-verified, brute-forced, both run | Exact, not statistical |
| The Lagrangian bound is tighter than the LP bound | paired **12.57 pp [9.49, 15.64]** | Strong as a difference, **not as a ratio** |

**The argument chain that ties them together** is in `docs/proposal_narrative.md` §2: profiles
drift → the whole batch must be re-optimised → the exact solver cannot sustain that → a fast
track makes the loop affordable. **The algorithm work exists because the loop demands it.**

---

## 4. Decisions taken, so they are not re-litigated

| | decision | who |
|---|---|---|
| O1 | No per-invocation cost term. Provisioning cost only | Closed |
| O10 | Reliability is a **floor**, anchored to baseline-delivered reliability. Not an objective | Advisor, 3 Sep |
| O9 | Scoped re-optimisation is **vacuous** — a drifted profile touches 84–100% of workflows. J9 re-optimises globally | Closed by F18 |
| §6.4 | Budget anchor replaced with a reference allocation | Accepted |
| §4.5 | EMA for latency, **decayed counting estimator for reliability** | Changed by F19 |
| Track A | Stays in the repo, **not reported in results** | Your call, this session |
| Track B | Keeps both roles — bound generator **and** allocator, with the 100× caveat attached | Your call, this session |

---

## 5. What must not be quoted

Three headline numbers were retracted after a statistical audit (F26, F27). **All three failed
the same way — a ratio of two means, which is not a typical ratio when either distribution has
a tail.**

| do not say | say instead |
|---|---|
| "~110× faster than the exact solver" | median speedup is **5×**; argue **bounded latency** — 0.106 ±0.020 s vs 12.3 ±10.3 s |
| "the bound is 3–6× tighter than the LP" | paired difference **12.6 pp [9.5, 15.6]**; median ratio ~2–2.5× |
| "consolidation halves Track C's gap" | **median improvement is 0.00%** — it fixes a rare, severe failure |

Full list in `docs/poc_findings_summary.md` under *"numbers that were corrected"*. **The rule:
never divide two means.** Report the paired difference and its interval.

This matters beyond honesty — **`mickie`'s slides and benchmark tables were generated before
the audit** and may carry the same defect.

---

## 6. The open questions, and who owns them

| # | question | owner | blocks |
|---|---|---|---|
| **O13** | Is `price(m)` independent of `gpu(m)`? | **Advisor / Murakkab paper** | T3's region, T1's arm comparison |
| **O12** | Is the closed loop a sufficient novelty claim? | **Advisor** | Chapter 2, and the framing of everything |
| **D1** | Formulation ratification, due 8 Sep | Team | Nominally everything, though §1 has not needed to change |
| — | Which duplicate implementation ships | 035 / 075 | The branch merge |
| — | Finding renumbering | Team | The branch merge |
| — | Reconcile the `[PROPOSED]` compatibility score with Hatherley (2025) | 077 | Any drift-detection number |

**O13 and O12 are advisor questions and both are cheap to ask.** O10 was answered in one
sentence this session and it materially improved the project — these two would too.

---

## 7. Suggested order for the next session

1. **Ask the advisor O12 and O13.** One message, and both shape what gets written.
2. **Reconcile the branches** using `BRANCHES.md`. Both are being worked on; they drift daily.
3. **Draft Chapter 3 from `D11_poc_report.md`**, restructured per `proposal_narrative.md` §6 so
   the loop leads and the optimizer serves it.
4. **Audit `mickie`'s slides and benchmark tables** against §5 above.
5. **Write the Semester 2 section** covering R7/R8/R9 as planned scope, with `prototype/` as
   evidence that R4/R5 are already de-risked.

---

## 8. Verifying the state yourself

```bash
python -m venv venv && venv/Scripts/activate
pip install -r requirements.txt
pytest poc/tests prototype/tests      # 586 pass, 4 skip
python -m poc.harness.runner          # the comparison table
```

Verified from a clean clone: fresh virtualenv, every figure reproduces byte-for-byte.

---

## 9. One thing worth carrying forward

Across this session, **every claim that broke was a bare ratio, and every claim that survived
had a mechanism behind it** — the fixture's arithmetic, the LP pricing by rate rather than by
whole instances, the loop holding reliability because it measures.

Three of the corrections came from someone asking a short sceptical question about a result
already presented as settled. That is worth saying in the presentation itself: an examiner who
sees the team volunteer what it got wrong will trust the rest considerably more.
