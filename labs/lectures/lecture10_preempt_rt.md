# Week-10 talk — PREEMPT_RT: what it changes in the kernel (40 min)

- **Precedes:** [lab10_preempt_rt.md](../lab10_preempt_rt.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. name why stock Linux has unbounded latency and what PREEMPT_RT changes.
2. run `cyclictest` with a defensible protocol.
3. read a latency histogram by its max, and place it against a deadline.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: the Hub runs Linux | tardiness is a reputation — today it becomes a histogram |
| 5–18 | Why stock Linux is late | non-preemptible sections, IRQs, locks |
| 18–28 | What PREEMPT_RT changes | threaded IRQs, sleeping spinlocks + PI, preemptible almost-everything |
| 28–34 | cyclictest and the protocol | what it measures and why ≥ 5 min under load |
| 34–37 | The scale change | MCU µs vs. Linux tens-of-µs — same theory |
| 37–40 | Bridge to the lab | the four-condition table decides the Hub |

## Segment 1 — Why stock Linux is late
- Key idea: between a timer firing and your thread running sit things priority
  can't jump: non-preemptible kernel sections, interrupt handlers for *anyone's*
  device, spinlock holders that must finish. On an MCU we owned every line; on
  Linux the "longest critical section" belongs to some driver we've never read.
- **Board sketch:** the wake-up path (timer IRQ → kernel → scheduler → thread) with
  the blockable gaps shaded — it's week 2's latency anatomy at a larger scale.
- **Question for the room:** which week-7 concept is "a driver holds a spinlock"?
  (Blocking — B_i by code we don't control.)

## Segment 2 — What PREEMPT_RT changes
- Key idea: make almost everything preemptible so priority means something end to
  end. IRQ handlers become kernel threads (schedulable — an RT task can outrank a
  NIC); spinlocks become rtmutexes that sleep and *inherit priority* (week 7's PIP,
  shipping inside the kernel); preemption reaches into the previously atomic paths.
- **Board sketch:** the same wake-up path, shaded gaps now sliced by preemption points.

> **Misconception to anticipate:** "the RT kernel makes Linux faster." Throughput
> usually gets *worse* — more preemption, more switches. It trades average
> performance for a bounded tail. If the histogram's mean improves but the max
> doesn't, you got nothing.

## Segment 3 — cyclictest and the protocol
- Key idea: cyclictest is the canonical instrument — a thread sleeps a fixed
  interval and logs (actual − expected) wake-up latency; the histogram of that is
  the kernel's promise, measured. Protocol discipline: RT priority (`-Sp90`),
  ≥ 5 min, and *under load* — an idle system's histogram is marketing. The max is
  the verdict; p99 is context.

## What about FreeRTOS?
Change of scale, same question: on the MCU the worst case came from a small kernel
(~µs); here it comes from a giant one (tens–hundreds of µs even with RT). That gap
— two orders of magnitude — is the number ADR-P1 (Linux vs. MCU partitioning) will
be built on.

## Bridge to the lab
Four conditions: stock/RT × idle/loaded. Predictions to write down before running:
stock-loaded's max is the scary one; RT-loaded's max lands well under the pump
loop's 10 ms — but nowhere near week 9's µs. The Hub Kit debuts today; groups merge.
