# Week 6 — Schedulability, response time and priority inversion
> - **Talk:** [06_schedulability](presentations/06_schedulability.md)
> - **Reading:** [READINGS.md](../READINGS.md), week 6 (includes the optional Lee & Seshia)
> - **Module:** 3
> - **The Problem Set goes out today** (exercises from chs. 2, 4 and 7 + RTA; due at the workshop, week 7).

**From:** Eng. Samuel Cifuentes — *"Daniela is asking whether she can add two more
sensors to the node. Answer like engineers: not 'let's try and see', but
'utilization lands at X, the test says Y, the worst response is Z'. Since I don't
trust theorems any more than I trust you, reproduce the famous case for me: a task
set that RM misses and EDF meets, on our board. Then watch the mutexes: Pathfinder
rebooted on Mars because of a priority inversion. Reproduce it here, where it costs
a laugh and not a mission. And before anyone says yes to Daniela: `calib` spins for
400 ms against a 1 s deadline, and the e-stop waits for control. Fix both at the
source."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Is R_i ≤ D_i for every task, blocking included? | Fig. 4.13 live; RTA as a script, fed with measured `C_i` and `B` |
| **Daniela** | Can the node take two more sensors? | U and the applicable test, with a verdict |
| **Edward** | Can a slow command delay the e-stop? | The inversion reproduced and closed; `calib` and the e-stop fixed at the source |

## What you'll measure

Hand in the prediction column before the lab.

| Measurement | Prediction | Your value | Reference |
|---|---|---|---|
| Fig. 4.13 under RM: who misses, when? | ____ | ____ | book: τ2 at t = 7 ms |
| Fig. 4.13 under EDF: misses in 60 s | ____ | ____ | book: none, U ≈ 0.97 ≤ 1 |
| Control's max R, no lock contention | ____ µs | ____ µs | your RTA script |
| Control's max R during the inversion (`k_sem` as lock) | ____ µs | ____ µs | — (that's what's broken) |
| Control's max R with a `k_mutex` | ____ µs | ____ µs | ≤ C + B + interference |
| B: the low thread's longest critical section | ____ µs | ____ µs | its GPIO pulse |
| `calib` CPU / duration, before the fix | ____ / ____ ms | ____ / ____ ms | it spins: CPU = duration |
| `calib` CPU / duration, after the fix | ____ / ____ ms | ____ / ____ ms | |
| E-stop, detection → valve low, max of 5 trips, before / after | ____ / ____ ms | ____ / ____ ms | sum the path in Task C |

## Tasks

### Task A — Fig. 4.13, live
- Implement the task set of the book's Fig. 4.13: τ1 (C = 2 ms, T = 5 ms) and τ2
  (C = 4 ms, T = 7 ms), "computation" being a calibrated busy-wait, one
  instrumentation GPIO per task. Run with RM priorities; capture the miss.
- Switch to EDF (`CONFIG_SCHED_DEADLINE=y`, same static priority for both). Before
  each thread blocks until its next release, give it that job's absolute deadline
  (`k_thread_absolute_deadline_set`). Set after the wake-up, the deadline comes too
  late: the thread was already chosen with the old one, and the run looks like RM.
  Verify it meets for 60 s.
- **Evidence:** two analyzer captures: the miss under RM, the success under EDF.

### Task B — The inversion, then the fix
- Three threads: control (high) and a slow console command (low) share a lock;
  telemetry (medium) does busy work and never touches the lock. First the lock is
  a `k_sem` of 1: that's how it breaks.
- Trigger the classic sequence: low takes the lock → high requests it → medium
  preempts low. Capture control's delay and annotate who runs in each segment.
- Replace the semaphore with a `k_mutex` (Zephyr does priority inheritance) and
  repeat. Mark the low thread's critical section with a GPIO: its width is B.
- **Evidence:** three annotated captures: no contention, inversion, PI mutex.

### Task C — Fix it at the source (ADR-005)

The utilization tests cover the periodic set. Two requirements fail whatever U says:

- **REQ-CONS-01.** `calib` needs ≈ 400 ms of CPU within its 1 s deadline, at the
  lowest priority. With Daniela's tasks, how much of that second do the tasks
  above the console leave it?
- **REQ-ESTOP-01.** Sampling detects the overpressure, but the valve only closes
  once control's next run sets the duty to 0 and the PWM step after it writes the
  pin. Add up the worst case from the periods: does it fit in 5 ms?

Measure the *before* case first. Unplug the flow input so `instr_flow` stays
idle, add `instr_set(&instr_flow, estop);` right after the e-stop check in
`task_sampling` to mark the detection, and clip a free analyzer channel on the
valve (GPIO21). `set 3300` trips the e-stop within ~2 s; `set 1500` then `clear`
resets it.

Then fix both where the time goes:

1. In `cmd_calib`, `k_busy_wait(400)` becomes `k_usleep(400)`: the console waits
   instead of spinning. Sleeps round up to the kernel tick, 100 µs on the S3
   (`CONFIG_SYS_CLOCK_TICKS_PER_SEC`). Do 1000 settles still fit in 1 s? What
   would a 1 kHz tick do?
2. In `task_sampling`, the branch that sets `estop` also sets `duty_pct = 0`, so
   the PWM step a few lines below drives the valve low in the same job.

- `instr_cons` now stays high while the console sleeps, so its width is the
  duration, not the CPU: take the CPU from a week-5 trace, as one settle's CPU
  × 1000. The 1000 sleeps flood the link, so the trace keeps only some of them.
- Redo the fit question and the e-stop sum for the new design.
- **Evidence:** the before/after rows, an e-stop capture of each, and both sums.

### Stretch (optional, not graded) — Jitter vs. control
- Inject a random 0–N ms delay before actuating in the flow loop. For N = 0, 2,
  5 ms, measure the loop error (deviation from the target flow). Needs the pump
  and the flow sensor.
- **Evidence:** error-vs-jitter table + one sentence: at which N does the loop stop being useful?

## Homework, due at the workshop

- **Does Daniela's load fit?** With the node's measured `C_i`, compute U and apply
  Liu & Layland and the hyperbolic test. Add Daniela's two tasks (parameters given
  in class) and repeat.
- **RTA as a script.** Implement `R_i = C_i + B_i + Σ⌈R_i/T_h⌉·C_h` in Python
  (book Fig. 4.17, about 15 lines), fed with the measured `C_i` and Task B's B.
  Does it bound rows 3 and 5? Why does a 30 s capture land below it?
- The workshop changes a parameter live and you re-run the script, so keep it in
  the repo, not in a notebook cell.

## What about FreeRTOS?

FreeRTOS ships fixed priorities only: no EDF in the kernel, so Task A can't be
reproduced as-is, and at U = 0.97 the professional answer is to redesign the set
until RM passes. Its mutexes (`xSemaphoreCreateMutex`) inherit priority, and its
binary semaphores allow Task B's exact mistake. The lesson is the same in both
kernels: across priorities, a PI mutex, never a bare semaphore.

## Deliverables (RET)

- **§2 ADR-002 — Node mutual-exclusion policy:** the PI mutex, where and why, with
  the measured B.
- **§2 ADR-005 — E-stop and `calib` fixed at the source:** context (the fit
  question and the e-stop sum), decision, before/after numbers.
- **§3 Week-6 evidence:** the Fig. 4.13 captures, the three lock captures, Task C's
  before/after captures.
- **§4 Schedulability:** U, both tests and the verdict on Daniela's load; the RTA
  script and its output, B included; the `calib` fit and the e-stop path, before
  and after ADR-005.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — 4.13 missing under RM (10) · EDF meeting (10) · inversion reproduced and closed with PI (10) · ADR-005 fix (10) | 40 |
| **Evidence** — captures of both schedulers (10) · the three lock regimes, annotated, with measured B (10) · Task C before/after (10) | 30 |
| **Analysis** — U and tests applied to Daniela's case (10) · RTA script vs. measurement, blocking included (10) · ADR-002 and ADR-005 with numbers (10) | 30 |
