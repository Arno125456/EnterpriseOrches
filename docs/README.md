# Documentation index

Nine documents, each with a different job. Nobody needs all of them. Find your row.

> Files are deliberately **not** grouped into subfolders yet — see `../BRANCHES.md`. A second
> branch is live and moving files now would make that merge much harder. Reorganise after.

---

## If you have one hour

| read | why |
|---|---|
| [`T0_briefing.md`](T0_briefing.md) | The 8 September session. The only thing with a deadline |
| [`poc_findings_summary.md`](poc_findings_summary.md) | What we believe now, at what confidence, and a table of numbers **not** to quote |

That is enough to hold a conversation about the project.

---

## By purpose

### Deciding something

| document | use it when |
|---|---|
| [`T0_briefing.md`](T0_briefing.md) | Ratifying the formulation. Structured as confirm-or-object with a default for every item |
| [`poc_findings_summary.md`](poc_findings_summary.md) | You need the current state of a claim, or need to check a number is still quotable |
| [`../BRANCHES.md`](../BRANCHES.md) | Before merging anything |

### Presenting or writing

| document | use it when |
|---|---|
| [`D11_poc_report.md`](D11_poc_report.md) | The PoC report for the advisor — four answers, the differentiator, limitations |
| [`proposal_narrative.md`](proposal_narrative.md) | Writing Chapter 3. The argument chain that makes the findings one story |
| [`study_guide.md`](study_guide.md) | Preparing to be questioned. Things to run and predict, not to read |

### Building

| document | use it when |
|---|---|
| [`System_Architecture_v2.md`](System_Architecture_v2.md) | The design of record. Amended nine times by measurement — those amendments are marked |
| [`component_reference.md`](component_reference.md) | You need to know how a component behaves and what it must become |
| [`../CLAUDE.md`](../CLAUDE.md) | Working summary and guardrails, including the scope guard |

### Evidence

| document | use it when |
|---|---|
| [`poc_findings.md`](poc_findings.md) | The full chronological log, 35 findings **including superseded ones**. Do not quote from it without checking the summary's corrections table |
| [`PoC_and_Validation_Plan.md`](PoC_and_Validation_Plan.md) | The September plan — scope, deliverables, schedule, risks |

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
