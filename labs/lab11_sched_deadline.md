# Week 11 — Periodic tasks in Linux: from CBS to SCHED_DEADLINE
> - **Reading:** [READINGS.md](../READINGS.md), week 11
> - **Module:** 5

**From:** Eng. Samuel Cifuentes — *"On the MCU, priorities were enough because we
controlled every line of code. On the Hub we don't: the GUI and the routing are
software we didn't write. I need the pump loop to have its CPU **guaranteed by
contract**, no matter what runs next to it. That exists, and it comes from theory
you've already seen: it's called SCHED_DEADLINE. Implement the loop as a periodic
task and prove the isolation to me."*

Today follows the book's ch. 12 almost to the letter (pthread + the ptask pattern).

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does the loop keep its period even if a neighbor goes rogue? | Misses under FIFO vs. DEADLINE with a "hog" running |
| **Edward** | Can a compromised process starve the loop? | With DEADLINE, the contract forbids it — demonstrated |

## What you'll measure

| Measurement (10 ms loop, ≥ 5 min) | Misses | Max jitter (µs) |
|---|---|---|
| `SCHED_FIFO` prio 90, quiet system | ____ | ____ |
| `SCHED_FIFO` prio 90 + **FIFO hog at prio 95** | ____ | ____ |
| `SCHED_DEADLINE` (runtime 2 ms / period 10 ms) + the same hog | ____ | ____ |

## Tasks

### Task A — The periodic task (ch. 12)
- Implement the pump loop as a periodic pthread with
  `clock_nanosleep(TIMER_ABSTIME)` and a miss counter — the book's ptask pattern
  (§12, code given).
- Instrument with an SBC GPIO (the analyzer is still the judge).
- **Evidence:** the loop running with misses = 0 on a quiet system.

### Task B — Priorities aren't enough
- Run the loop with `chrt -f 90`. Launch the "hog": a busy-loop with `chrt -f 95`
  (a misassigned priority — a realistic integration mistake).
- Fill in row 2. The loop starves: capture it.
- **Evidence:** miss count + capture of the frozen GPIO.

### Task C — The CBS contract
- Same task, now `sched_setattr` with `SCHED_DEADLINE` (runtime 2 ms,
  deadline = period = 10 ms). The same hog next to it.
- Fill in row 3. Connect it to theory in two sentences: runtime/period is the
  CBS's `U_s = Q_s/T_s` — the isolation the book promises, observed.
- **Evidence:** misses = 0 under the hog + the two sentences in the RET.

## What about FreeRTOS?

No equivalent: FreeRTOS (and Zephyr) give you priorities, not *CPU contracts*. On
an MCU you prevent Task B's hog by reviewing your own code; in a system running
third-party software that review is impossible — that's why reservation-based
scheduling lives in Linux, and why the Hub needs it.

## Deliverables (RET)

- **§3 Week-11 evidence:** the three-regime table + captures.
- **§4:** the Hub loop's budget as a CBS: chosen `U_s` and its margin (Task A's
  measured runtime + a justified cushion).

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — correct ptask periodic task (15) · starvation reproduced (10) · DEADLINE isolating (15) | 40 |
| **Evidence** — complete table + captures of the three regimes (30) | 30 |
| **Analysis** — CBS↔SCHED_DEADLINE connection in their own words (15) · justified `U_s` budget (15) | 30 |
