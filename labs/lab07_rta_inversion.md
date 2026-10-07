# Week 7 — RTA and priority inversion
> - **Reading:** [READINGS.md](../READINGS.md), week 7
> - **Module:** 3
> - **Problem Set 2 goes out today** (exercises from ch. 7 + RTA; due week 9).

**From:** Eng. Samuel Cifuentes — *"The utilization test tells me whether the set
fits; it doesn't tell me **how long each task takes in the worst case** — and the
e-stop has a 5 ms deadline, not a percentage. Implement RTA as a script, fed with
the measured C_i. And watch the mutexes: Pathfinder rebooted on Mars because of a
priority inversion. Reproduce it here, where it costs a laugh and not a mission."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Is R_i ≤ D_i for *every* task, blocking included? | RTA as a script + measured B_i |
| **Edward** | Can a slow malicious command delay the e-stop? | The inversion: reproduced and closed with PI |

## What you'll measure

| Measurement | Your value | RTA prediction |
|---|---|---|
| Max R of the control task (no mutex) | ____ µs | ____ µs |
| Max R of control **during the inversion** | ____ µs | — (that's what's broken) |
| Max R of control with a PI mutex | ____ µs | ≤ C + B_i + interference: ____ µs |
| Real B_i (longest critical section of the third task) | ____ µs | |

## Tasks

### Task A — RTA as a tool
- Write the (Python) script for the recurrence `R_i = C_i + Σ⌈R_i/T_h⌉·C_h`
  (book Fig. 4.17) and feed it the node's measured `C_i`.
- Verify: does the R it predicts for control match the maximum observed over a
  30 s capture? (Why only "almost"? — the worst case is rare; write that down.)
- **Evidence:** the script in the repo + output vs. measurement.

### Task B — The inversion, live
- Three threads: control (high) and slow-console (low) share a mutex **without PI**
  (a `k_sem` of 1 used as a lock — that's how it breaks); telemetry (medium)
  doesn't use the lock.
- Trigger the classic sequence: low takes the lock → high requests it → medium
  preempts low. Capture the high task's delay.
- **Evidence:** analyzer capture with the inversion annotated (who runs in each segment).

### Task C — The fix
- Replace it with `k_mutex` (Zephyr does priority inheritance). Repeat the
  sequence; fill in rows 3–4. Extend your script: `R_i = C_i + B_i + interference`.
- **Evidence:** the "after" capture + extended RTA matching the measurement.

## What about FreeRTOS?

FreeRTOS mutexes (`xSemaphoreCreateMutex`) also inherit priority — and its binary
semaphores also allow Task B's exact mistake. The lesson is identical in both
kernels: for mutual exclusion across priorities, a PI mutex, never a bare semaphore.

## Deliverables (RET)

- **§4:** full RTA of the real task set (script + output), with B_i.
- **§3 Week-7 evidence:** the three captures (no lock / inversion / PI).
- **§2 ADR-002 — Node mutual-exclusion policy** (PI mutex, where and why).

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — correct RTA script (15) · inversion reproduced (15) · closed with PI (10) | 40 |
| **Evidence** — annotated captures of the three regimes (20) · measured B_i (10) | 30 |
| **Analysis** — RTA vs. measurement well read (15) · ADR-002 with numbers (15) | 30 |
