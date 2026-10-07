# Week-12 talk — Linux RT in practice: affinity, isolation, mixed loads (40 min)

- **Precedes:** [lab12_isolation.md](../lab12_isolation.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. name the interference channels a DEADLINE contract does *not* close.
2. compose the layered isolation recipe (contract + affinity + isolcpus + IRQ steering) and say what each layer removes.
3. write a deployment configuration another team can replicate.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: dress rehearsal | this rig *is* the project's checkpoint 2 |
| 5–17 | What the contract doesn't cover | IRQs, kernel housekeeping, shared caches |
| 17–29 | The layered recipe | four layers, each killing one interference channel |
| 29–34 | Reproducibility as a deliverable | config as commands, justified line by line |
| 34–37 | What about FreeRTOS? | isolation is trivial when you own all the code |
| 37–40 | Bridge to the lab | three configurations, watch the tail collapse |

## Segment 1 — What the contract doesn't cover
- Key idea: week 11 secured *CPU time*; interference has other doors. Device IRQs
  land on your core and preempt even DEADLINE (below the IRQ threads you don't
  control); kernel housekeeping (ticks, RCU callbacks) runs everywhere by default;
  and memory-system interference — a neighbor thrashing the shared cache/bus slows
  your instructions without stealing one scheduler slot (week 3's silicon lesson,
  now multi-core).
- **Board sketch:** the pump loop's core with three arrows landing on it: IRQ,
  tick/RCU, cache traffic — label which mechanism closes each.

## Segment 2 — The layered recipe
- Key idea: one layer per channel. `SCHED_DEADLINE` → CPU time. Affinity
  (`sched_setaffinity`/`taskset`) → placement. `isolcpus nohz_full rcu_nocbs` →
  evict the scheduler's other clients and the housekeeping from that core.
  `/proc/irq/*/smp_affinity` → send device interrupts elsewhere. The lab's table
  has one row per layer added — each row should visibly eat tail.
- **Board sketch:** the four layers as concentric fences around core 3.
- **Question for the room:** which layers did week 9's AMP give us for free? (All
  of them — a dedicated core is this recipe implemented in silicon; Linux needs it
  spelled out because the box is shared.)

> **Misconception to anticipate:** "isolcpus alone is enough." Unpinned IRQs still
> land there, and without the contract a rogue FIFO task pinned to the same core
> still wins. No single layer survives alone — that's why the table has three rows,
> not one.

## Segment 3 — Reproducibility as a deliverable
- Key idea: a configuration that lives in someone's shell history dies at
  deployment. ADR-004 is the recipe as literal commands/cmdline, each line citing
  the table row that justifies it. Edwin's bar: another group replicates it in
  10 minutes.

## What about FreeRTOS?
FreeRTOS SMP has affinity (`vTaskCoreAffinitySet`) and isolation is "put nothing
else on that core" — feasible because every task is yours. Linux needs four layers
because the box runs software you don't own. Same principle as week 9: partitioning
cuts tails; a more hostile ecosystem just needs more fencing.

## Bridge to the lab
Full interference (synthetic GUI render + `iperf3` bursts) against three
configurations. Expected shape: the max collapses as layers stack; the last row's
number is the one the project inherits. Content closes today — everything after
this is the Hub.
