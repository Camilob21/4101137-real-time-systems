# Week 6 — Schedulability: the theory, put to the test
> - **Reading:** [READINGS.md](../READINGS.md), week 6 (includes the optional Lee & Seshia)
> - **Module:** 3
> - **Problem Set 1 goes out today** (exercises from chs. 2 and 4; due at the workshop, week 8).

**From:** Eng. Samuel Cifuentes — *"Daniela is asking whether she can add two more
sensors to the node. Today you answer like engineers: not 'let's try and see', but
'utilization lands at X, the test says Y'. And since I don't trust theorems any
more than I trust you, reproduce the famous case for me: a task set that RM misses
and EDF meets — on our board, not in the book."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does more load fit on the node? | U computed from measured `C_i` + the applicable test |
| **Daniela** | What if irrigation is *a little* late? | The loop with induced jitter: the degradation, measured |

## What you'll measure

| Measurement | Your value | Prediction |
|---|---|---|
| U of the synthetic task set (3 tasks) | ____ | designed at U ≈ 0.97 |
| Deadline miss under RM (which task, when?) | ____ | theory says: yes, it misses (Fig. 4.13) |
| Deadline miss under EDF | ____ | theory says: U ≤ 1 ⇒ it meets |
| Flow-loop error with induced jitter of 0 / 2 / 5 ms | ____ / ____ / ____ | grows with jitter |

## Tasks

### Task A — Fig. 4.13, live
- Implement the task set from the book's Fig. 4.13 (periods and computation times
  given; "computation" is a calibrated busy-wait). Run with RM priorities; capture
  the miss.
- Switch to EDF (`CONFIG_SCHED_DEADLINE=y`, same static priority,
  `k_thread_deadline_set` each period). Verify it meets.
- **Evidence:** two analyzer captures — the miss under RM, the success under EDF.

### Task B — Does the new load fit?
- With the real node's measured `C_i`: compute U, apply Liu & Layland and the
  hyperbolic test. Add "Daniela's two tasks" (parameters given in class) and repeat.
- **Evidence:** the calculation in RET §4, with a verdict and which test backs it.

### Task C — Jitter vs. control (the bridge to control theory)
- Inject artificial jitter into the flow loop (random 0–N ms delay before
  actuating). For N = 0, 2, 5 ms: measure the loop error (deviation from target
  flow, or from the course rig's setpoint).
- **Evidence:** error-vs-jitter table + one sentence: at which N does the loop stop being useful?

## What about FreeRTOS?

FreeRTOS only ships fixed priorities — there is no EDF in the kernel. Task A can't
be reproduced as-is: with U = 0.97 and FreeRTOS, the professional answer is to
redesign the task set until it passes the RM test (or lower U). That constraint is
real in industry — and it's why the book spends half a chapter on RM.

## Deliverables (RET)

- **§4 Schedulability:** U, both tests, verdict on Daniela's load.
- **§3 Week-6 evidence:** Fig. 4.13 captures + jitter-vs-control table.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — 4.13 task set missing under RM (15) · EDF meeting (15) · jitter injected (10) | 40 |
| **Evidence** — captures of both regimes (15) · error-vs-jitter table (15) | 30 |
| **Analysis** — U and tests correctly applied to Daniela's case (20) · control-jitter reading (10) | 30 |
