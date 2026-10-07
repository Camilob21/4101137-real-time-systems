# Week-7 talk — Response-time analysis and priority inversion (40 min)

- **Precedes:** [lab07_rta_inversion.md](../lab07_rta_inversion.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. run the RTA recurrence by hand for a small set.
2. narrate the priority-inversion sequence and why priorities alone don't prevent it.
3. state the PIP fix and bound B_i.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: Pathfinder reboots on Mars | a solved 1997 mystery, diagnosed by trace |
| 5–17 | RTA: per-task worst case | the recurrence, iterated to a fixed point |
| 17–27 | The inversion, step by step | low holds, high waits, medium runs |
| 27–33 | PIP and the blocking bound | inherit priority; B_i enters the RTA |
| 33–37 | What about FreeRTOS? | mutex inherits, binary semaphore doesn't — same trap |
| 37–40 | Bridge to the lab | reproduce it, fix it, predict it |

## Segment 1 — RTA: per-task worst case
- Key idea: utilization says the *set* fits; the e-stop has a 5 ms deadline, not a
  percentage — it needs *its own* worst case. R_i = C_i + Σ⌈R_i/T_h⌉·C_h over
  higher-priority tasks, iterated until it stops moving (Fig. 4.17). Fifteen lines
  of Python, fed with measured C_i — a tool, not a theorem.
- **Board sketch:** run the iteration live on the node's real numbers, watching R
  converge.
- **Question for the room:** why will the 30 s capture's max be slightly *below*
  the RTA's R? (The critical instant is rare — write that down for Task A.)

## Segment 2 — The inversion, step by step
- Key idea: three actors — low holds a lock, high blocks on it, medium (no lock
  involved) preempts low. High now waits on *medium*: priority inverted, unbounded
  by design. Pathfinder: bus-management task (high) + meteo task (low) shared a
  mutex; comms (medium) starved low; the watchdog rebooted the lander until JPL
  replayed the trace on Earth.
- **Board sketch:** the classic three-band timeline; shade the interval where
  "highest priority" is a lie.
- **Question for the room:** which of our threads plays each role? (Control /
  telemetry / console — this afternoon's Task B.)

## Segment 3 — PIP and the blocking bound
- Key idea: priority inheritance — while low holds the lock, it borrows high's
  priority, so medium can't intervene. The wait doesn't vanish; it becomes
  *bounded*: B_i = the longest critical section(s) that can block task i
  (Theo. 7.2), and the RTA extends to R_i = C_i + B_i + interference. One slide on
  PCP: ceilings, no deadlock, at most one blocking — worth knowing it exists.

> **Misconception to anticipate:** "a semaphore is a mutex." A binary semaphore has
> no owner, so nothing can inherit through it — it *allows* the inversion. Mutual
> exclusion across priorities → PI mutex, always.

## What about FreeRTOS?
`xSemaphoreCreateMutex` inherits priority, exactly like `k_mutex`; FreeRTOS binary
semaphores allow Task B's mistake, exactly like `k_sem`. Pathfinder ran VxWorks —
the fix was flipping one mutex attribute. Kernel-independent lesson.

## Bridge to the lab
Three regimes, three captures: no contention, inversion (bare semaphore), PI mutex.
The extended RTA script should predict regime 3's max within measurement noise —
prediction and trace agreeing is the whole point of the module. Problem Set 2 goes
out today.
