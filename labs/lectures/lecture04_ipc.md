# Week-4 talk — IPC: message queues, workqueues, ISR deferral (40 min)

- **Precedes:** [lab04_ipc.md](../lab04_ipc.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. pick the right kernel primitive for each superloop pattern.
2. explain the short-ISR + deferral discipline.
3. read an A/B table by maxima, not averages.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: Samuel defends the A/B to Gustavo | the table decides the architecture |
| 5–18 | The full mapping table | every superloop piece → its kernel counterpart |
| 18–28 | ISR deferral discipline | why ISRs must be short and where the work goes |
| 28–33 | Reading an A/B | maxima move, averages barely do |
| 33–37 | What about FreeRTOS? | 1:1 mapping, different defaults |
| 37–40 | Bridge to the lab | protocol symmetry or the table lies |

## Segment 1 — The full mapping table
- Key idea: migration is a table, not an art form (it's printed in the lab guide):
  ISR flag + loop check → short ISR + `k_msgq`/`k_sem`; heavy polled work → thread
  with its own priority; improvised bottom half → `k_work`; blocking console →
  low-priority thread. Each row removes one coupling the superloop forced.
- `k_msgq` vs. `k_sem`: a queue carries data (the tick's release time, from week
  3); a semaphore only says "go" (sampling waking control every 10th sample).
  Pick the lighter one when there is nothing to carry.
- **Every thread blocks.** The superloop's habit of polling doesn't survive the
  move: a thread that never sleeps owns every cycle below it — idle included.
  The lab's console polls, then naps 5 ms.
- `main` now brings the hardware up and returns. At its default priority 0 it
  outranks every thread, so bring-up completes before any of them runs — the
  week-3 `CONFIG_MAIN_THREAD_PRIORITY=10` goes away.
- **Board sketch:** the table, filled row by row with the class naming the
  counterpart before it's written.
- **Question for the room:** which row kills the blocking-command problem, and why
  doesn't the console need to be *fixed* — just deprioritized?

## Segment 2 — ISR deferral discipline
- Key idea: interrupt context blocks everything above it — work done there is
  latency charged to *every* task. Rule: ISR captures and hands off (µs), a thread
  or `k_work` processes. The workqueue is a shared thread: convenient, but its
  queue is FIFO — heavy items delay light ones (own thread if it matters).
- **The trap:** Zephyr's *system* workqueue runs at priority −1 — cooperative.
  Work submitted there can't be preempted by any preemptive thread, sampling
  included. The lab starts its own queue at priority 5 with
  `k_work_queue_start`.
- **Question for the room:** the flow batch is float math on a core with its FPU
  off. On the system workqueue, what does it do to sampling's jitter? (Adds the
  whole batch — tens of µs on the S3 — to it.)
- **Board sketch:** timeline of a long ISR stretching every task's latency vs. the
  short-ISR + hand-off version.

> **Misconception to anticipate:** "threads make the system faster." They don't —
> context switches cost. What they buy is that the worst case stops depending on
> unrelated code. The A/B shows the average nearly tied and the max transformed.

## Segment 3 — Reading an A/B
- Key idea: same tasks, same board, same protocol, one variable (the architecture).
  Compare maxima: Samuel's question is the worst case. And report the cost too
  (switch overhead) — an ADR that hides the cost isn't credible to Gustavo.

## What about FreeRTOS?
`k_msgq` → `xQueue`, `k_sem` → semaphores, `k_work` → the timer-daemon task or a
dedicated worker. Same discipline, same table. The real difference is defaults:
FreeRTOS boots minimal (its strength on small chips); Zephyr ships console/log/shell
ready (its strength in bigger products).

## Bridge to the lab
Finish the migration, keep the *same* instrumentation GPIOs, repeat the week-2
protocol exactly. Expected shape: averages ≈ tied, max jitter under the blocking
command collapses from hundreds of ms to µs, and control stops stalling too —
that pair of numbers is ADR-001's justification. The cost gets measured on the
same capture: the gap between `instr_samp` falling and `instr_ctrl` rising is a
context switch.

## References
- Buttazzo, §10.6–10.7 (the week's reading): CABs vs. message queues, and kernel
  overhead as something to measure.
- Zephyr docs: *Workqueue threads* —
  docs.zephyrproject.org/latest/kernel/services/threads/workqueue.html (the
  system queue's cooperative priority, `k_work_queue_start`); *Message queues* and
  *Semaphores* — docs.zephyrproject.org/latest/kernel/services/data_passing/message_queues.html,
  docs.zephyrproject.org/latest/kernel/services/synchronization/semaphores.html
- Zephyr docs: *Thread analyzer* —
  docs.zephyrproject.org/latest/services/debugging/thread-analyzer.html (Task D).
