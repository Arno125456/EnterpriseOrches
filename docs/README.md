# Documentation index

**If you are new, read [`ORIENTATION.md`](ORIENTATION.md) first** — the whole project in one
file, assuming no prior knowledge, with pointers into everything below.

Sixteen documents, each with a different job. Nobody needs all of them. Find your row.

## The shape of this folder

Grouped by **what you are trying to do**, not by document type:

```
docs/
  ORIENTATION.md      <- start here if you are new. The whole project, one file
  README.md           <- this index
  REPO_GUIDE.md       <- every file in the repository, explained one by one

  design/             how the system is built    architecture / components / diagrams
  evidence/           what we measured           findings log / summary / benchmarks
  proposal/           what we are writing        narrative / report / plan / slides
  sessions/           what we run with people    T0 briefings / study guide
  presentation/       the T0 deck (open in a browser)

  research_papers/    literature tracking, feeds Chapter 2
  v1_superseded/      the retired v1 design. Not current
```

**The rule of thumb:** `design/` says how it *should* work, `evidence/` says what it
*actually* did. Where those two disagree, `evidence/` wins and `design/` gets amended -
which has happened nine times, and each amendment is marked in place.

---

## If you have one hour

| read | why |
|---|---|
| [`ORIENTATION.md`](ORIENTATION.md) | **Start here.** The whole project from zero — problem, design, findings, where to go deeper |
| [`T0_briefing.md`](sessions/T0_briefing.md) | The 8 September session. The only thing with a deadline |
| [`poc_findings_summary.md`](evidence/poc_findings_summary.md) | What we believe now, at what confidence, and a table of numbers **not** to quote |

That is enough to hold a conversation about the project.

---

## By purpose

### Understanding the project at all

| document | use it when |
|---|---|
| [`ORIENTATION.md`](ORIENTATION.md) | You are new, or you want one file that covers problem, design, findings and next steps |
| [`pipeline.md`](design/pipeline.md) | You want the ASCII diagrams — input construction, invariant gating, track execution, metrics |

### Deciding something

| document | use it when |
|---|---|
| [`T0_briefing.md`](sessions/T0_briefing.md) | **Running** the 8 Sep session. Confirm-or-object, a default for every item, sign-off template |
| [`T0_Formulation_Ratification_Briefing.md`](sessions/T0_Formulation_Ratification_Briefing.md) | The **formal statement** of the model being ratified — the mathematics and the problem classification |
| [`poc_findings_summary.md`](evidence/poc_findings_summary.md) | You need the current state of a claim, or need to check a number is still quotable |
| [`../BRANCHES.md`](../BRANCHES.md) | Before merging anything |

### Presenting or writing

| document | use it when |
|---|---|
| [`D11_poc_report.md`](proposal/D11_poc_report.md) | The PoC report for the advisor — four answers, the differentiator, limitations |
| [`proposal_narrative.md`](proposal/proposal_narrative.md) | Writing Chapter 3. The argument chain that makes the findings one story |
| [`study_guide.md`](sessions/study_guide.md) | Preparing to be questioned. Things to run and predict, not to read |
| [`M1_Proposal_Presentation_Slides.md`](proposal/M1_Proposal_Presentation_Slides.md) | Building the M1 deck. Slide-by-slide with speaker scripts — **check every figure against the corrections table first** |
| [`chapter3_benchmark_results.md`](evidence/chapter3_benchmark_results.md) | You need the scale benchmark tables or their LaTeX. Note its §1 summary was corrected by F32 |

### Building

| document | use it when |
|---|---|
| [`System_Architecture_v2.md`](design/System_Architecture_v2.md) | The design of record. Amended nine times by measurement — those amendments are marked |
| [`component_reference.md`](design/component_reference.md) | You need to know how a component behaves and what it must become |
| [`../CLAUDE.md`](../CLAUDE.md) | Working summary and guardrails, including the scope guard |

### Evidence

| document | use it when |
|---|---|
| [`poc_findings.md`](evidence/poc_findings.md) | The full chronological log, 35 findings **including superseded ones**. Do not quote from it without checking the summary's corrections table |
| [`PoC_and_Validation_Plan.md`](proposal/PoC_and_Validation_Plan.md) | The September plan — scope, deliverables, schedule, risks |

### Archive

| | |
|---|---|
| [`v1_superseded/`](v1_superseded/) | The retired v1 design. Not current — its README says what replaced what and why |
| [`research_papers/`](research_papers/) | Literature tracking, feeds Chapter 2 |

---

## How the results documents relate

They form a stack, and the order matters:

```
proposal_narrative.md    what the findings are FOR      -- the argument
        |
poc_findings_summary.md  what we believe NOW            -- current state + corrections
        |
poc_findings.md          what happened, in order        -- full evidence, incl. retracted
```

**Read down, not up.** The log contains findings that were later corrected or retracted —
F14 was corrected by F15 and again by F16, F7's headline by F30, F16's speedup by F29. The
summary states the current position; the log preserves how it got there.

---

## The one rule for quoting a number

Check the summary's **"numbers that were corrected"** table first. Seven claims made during
the PoC are wrong or overstated as written, including three headline figures. All three
failed the same way — a ratio of two means — so **treat any bare `N×` claim as unverified
unless an interval is attached**.
