# Week 5 — Tracing: seeing what the analyzer can't
> - **Talk:** [05_tracing](presentations/05_tracing.md) · **Tech guide:** [SOP-05](sops/sop05_tracing.md)
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

Hand in the prediction column before the lab.

| Measurement | Prediction | Your value | Contrast |
|---|---|---|---|
| Context switch per the trace | ____ µs | ____ µs | vs. GPIO (wk 4): ____ µs |
| Tick ISR → sampling start per the trace | ____ µs | ____ µs | vs. `lat_peak_us`: ____ µs |
| Per-thread CPU load (%) in normal operation | | ____ | sums ≈ 100 % with idle and the tracer |
| Tracing overhead on max sampling jitter | ____ µs | ____ µs | analyzer, tracing on vs. off |

## Tasks

### Task A — Enable tracing
- Stream CTF out of the S3's UART jack at 4 Mbaud (SOP-05): two build files, no C
  changes. In this build the console moves to the USB jack.
- **Evidence:** first trace open in the viewer, with the node's threads named.

### Task B — The story of one preemption
- Type `calib` and capture 1–2 s. Find one tick inside it and name the chain: tick
  ISR → sampling ready (the ISR's `k_msgq_put`) → console preempted (ready, not
  blocked) → sampling runs (`instr_samp` rises) → sampling pends (its `k_msgq_get`
  blocks) → back to the console. Only the first ≈ 75 ms of `calib` survive: why?
- Find a 10th tick: where does `k_sem_give` send the CPU instead?
- Note the timestamps and compare against the GPIO measurement and `lat_peak_us`.
- **Evidence:** annotated trace screenshot (arrows over the events).

### Task C — The price of looking
- Tracing is load too. Measure sampling jitter (usual protocol, via GPIO) with
  tracing on and off; fill in row 4.
- **Evidence:** both captures + the delta.

## What about FreeRTOS?

Same concept, different tools: the kernel's trace macros stay empty until a
recorder fills them, Percepio Tracealyzer (commercial) or SEGGER SystemView. Under
ESP-IDF on the S3, app_trace streams SystemView data over the same USB jack. The
transferable lesson is about instruments: every observer perturbs, which is why
this course measures *with* GPIO and explains *with* traces.

## Deliverables (RET)

- **§3 Week-5 evidence:** table + the annotated preemption trace.
- **§1:** from now on, note next to each `C_i` which instrument measured it.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — tracing working with named threads (20) · preemption captured (20) | 40 |
| **Evidence** — complete table with both instruments (20) · readable annotated trace (10) | 30 |
| **Analysis** — trace vs. GPIO explained (why do they differ?) (15) · tracing overhead read correctly (15) | 30 |
