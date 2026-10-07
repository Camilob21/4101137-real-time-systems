# Week 5 — Tracing: seeing what the analyzer can't
> - **Tech guide:** [SOP-05](sops/sop05_tracing.md)
> - **Reading:** [READINGS.md](../READINGS.md), week 5
> - **Module:** 4

**From:** Eng. Samuel Cifuentes — *"The logic analyzer sees pins; I need to see the
**scheduler**: who ran, when, why, and who waited. Next week we start
schedulability analysis and I refuse to argue over assumptions. Instrument the node
with tracing and bring me the first trace showing a complete preemption."*

GPIO + analyzer stays the judge of the *numbers* (it doesn't perturb); tracing is
the judge of the *story* (who and why). They're used together.

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Can I see a preemption, not infer it? | Trace with the exact instant of the switch |
| **Edwin** | In the field, how do I diagnose without an analyzer? | Tracing travels inside the firmware |

## What you'll measure

| Measurement | Your value | Contrast |
|---|---|---|
| Context switch per the trace | ____ µs | vs. GPIO (wk 4): ____ µs |
| ISR → thread latency per the trace | ____ µs | vs. GPIO: ____ µs |
| Per-thread CPU load (%) in normal operation | ____ | sums ≈ 100 % with idle |
| Tracing overhead on sampling jitter | ____ µs | measured with GPIO, tracing on/off |

## Tasks

### Task A — Enable tracing
- Turn on Zephyr's tracing subsystem in the node (SystemView if you have a probe;
  CTF over UART if not — the SOP covers both routes).
- **Evidence:** first trace open in the viewer, with the node's threads named.

### Task B — The story of one preemption
- Generate a flow event while the console runs: capture in the trace the chain
  ISR → `k_msgq` → thread wake-up → preemption of the console.
- Note the timestamps and compare against the GPIO measurement.
- **Evidence:** annotated trace screenshot (arrows over the events).

### Task C — The price of looking
- Tracing is load too. Measure sampling jitter (usual protocol, via GPIO) with
  tracing on and off; fill in row 4.
- **Evidence:** both captures + the delta.

## What about FreeRTOS?

Same concept, different tools: `configUSE_TRACE_FACILITY` + Tracealyzer
(commercial) or SystemView. The transferable lesson is about instruments: every
observer perturbs — which is why this course measures *with* GPIO and explains
*with* traces.

## Deliverables (RET)

- **§3 Week-5 evidence:** table + the annotated preemption trace.
- **§1:** from now on, note next to each `C_i` which instrument measured it.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — tracing working with named threads (20) · preemption captured (20) | 40 |
| **Evidence** — complete table with both instruments (20) · readable annotated trace (10) | 30 |
| **Analysis** — trace vs. GPIO explained (why do they differ?) (15) · tracing overhead read correctly (15) | 30 |
