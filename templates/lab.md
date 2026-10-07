# Week N — <Session title>
> - **Tech guide:** [SOP-NN](sop.md) *(delete this line if the session has no SOP)*
> - **Reading:** [READINGS.md](../READINGS.md), week N
> - **Module:** M

**From:** `<Stakeholder>` (`<role>`) — *"<The problem, in one or two sentences from the project.>"*

<One paragraph: what gets built/measured today and why it matters. Close with:>
**Mission:** <one operational sentence>.

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **`<Name>`** | `<question>` | <measurable answer> |

## What you'll measure

<The table this session must fill in — columns defined, cells empty:>

| Measurement | Your value | Target | Note |
|---|---|---|---|
| <e.g. loop p99 jitter> | ____ µs | < ___ µs | `<condition>` |

## Tasks

### Task A — `<name>`
- <minimal steps; exact commands go in the SOP>
- **Evidence:** <log / analyzer capture / filled table>

### Task B — `<name>`
- ...
- **Evidence:** ...

## What about FreeRTOS?

<3–5 lines: the equivalent API (`xTaskCreate`/`xQueueSend`/...), what changes, and
when choosing FreeRTOS would be the right call. Nothing installed — it's a comparison.>

## Deliverables (RET)

- **§1 Task set:** <which row is added/updated, with measured C_i>
- **§2 ADR-NNN:** <today's decision: context, decision, numbers, status>
- **§3 Week-N evidence:** the table above, filled in, with a one-sentence reading.
- **§4 Schedulability:** <if applicable: U, test used, RTA>

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — `<item>` (xx) · `<item>` (xx) | 40 |
| **Evidence** — table complete and well read (xx) · traces attached (xx) | 30 |
| **Analysis** — ADR justified with numbers (xx) · `<item>` (xx) | 30 |
