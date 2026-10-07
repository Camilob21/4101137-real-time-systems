# Week-5 talk — Instrumented measurement: tracing (40 min)

- **Precedes:** [lab05_tracing.md](../lab05_tracing.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. explain what a scheduler trace shows that GPIO can't.
2. describe the tracing pipeline (events → transport → viewer).
3. design a measurement that accounts for its own overhead.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: the analyzer sees pins, not decisions | *who ran, when, why* needs a new instrument |
| 5–15 | The tracing pipeline | kernel events, transport (RTT/UART/CTF), viewer |
| 15–27 | Reading a trace | one preemption, narrated event by event (live demo) |
| 27–33 | The observer effect | every instrument perturbs; measure vs. explain |
| 33–37 | What about FreeRTOS? | trace facility + Tracealyzer/SystemView |
| 37–40 | Bridge to the lab | the annotated preemption + the overhead delta |

## Segment 1 — The tracing pipeline
- Key idea: the kernel already emits events (switch in/out, ready, ISR enter/exit,
  IPC ops); tracing turns them on and ships them out — SystemView over RTT with a
  probe, or CTF over UART without one (both routes in SOP-05). The viewer
  reconstructs the timeline with names.
- **Board sketch:** node → event buffer → transport → viewer, with the two
  transport routes forking.

## Segment 2 — Reading a trace (demo)
- Key idea: a trace answers *why*: the flow ISR fires mid-console, posts to the
  queue, the control thread becomes ready, preempts, runs, yields back. Walk it
  live on last week's node if the room allows; otherwise a canned capture.
- **Board sketch:** the thread-lane view — one lane per thread, arrows at each
  event of the chain.
- **Question for the room:** where in this picture is the number GPIO gave us last
  week? (The gap between two events — the trace *contains* the GPIO story.)

## Segment 3 — The observer effect
- Key idea: emitting events costs CPU and can shift the very latencies under study.
  Course discipline: GPIO + analyzer stays the judge of *numbers* (passive);
  tracing is the judge of the *story*. Task C measures tracing's own overhead —
  the instrument gets instrumented.

> **Misconception to anticipate:** "the trace timestamps are ground truth."
> They're the truth *as perturbed by tracing*. Cross-checking trace vs. GPIO (the
> lab's table) is the habit that catches instrument lies.

## What about FreeRTOS?
Same concept, different plumbing: `configUSE_TRACE_FACILITY` + Tracealyzer
(commercial) or SystemView. The transferable lesson is instrument design: know what
each observer costs before believing it.

## Bridge to the lab
Two deliverables define success: a preemption chain annotated arrow-by-arrow in the
viewer, and the overhead row — sampling jitter with tracing on vs. off, measured by
GPIO. Next week the schedulability claims start; from now on every claim can be
checked against a trace.
