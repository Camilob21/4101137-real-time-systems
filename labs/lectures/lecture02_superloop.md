# Week-2 talk — The vocabulary: taxonomy, task models, latency anatomy (40 min)

- **Precedes:** [lab02_superloop.md](../lab02_superloop.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. classify a task as hard/firm/soft by the *consequence of a miss*.
2. name each component of the interrupt→response chain and where jitter comes from.
3. write a measurable timing requirement in EARS form with an ID.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: Samuel's memo | measure what we have before pitching a kernel |
| 5–15 | The taxonomy + task model | H/F/S by consequence; T_i, C_i, D_i, jitter |
| 15–25 | Latency anatomy | the interrupt→response chain, delay by delay |
| 25–35 | Requirements you can measure (EARS) | from "fast enough" to a testable sentence |
| 35–40 | Bridge to the lab | the baseline table and what numbers to expect |

## Segment 1 — Taxonomy + task model
- The taxonomy is defined by what a miss *costs*, and Buttazzo (§2.2) gives it a
  picture worth drawing: the **value function** v(t) of a result finished at time t.
  - **Hard**: after the deadline the value is not zero — it's *negative*
    (damage). Node example: the overpressure e-stop; a late close bursts a hose.
  - **Firm**: value drops to zero after the deadline; the late result is useless
    but harmless. Node example: the console reply — a stale answer helps nobody,
    hurts nobody.
  - **Soft**: value *decays* after the deadline; late still helps. Node example:
    telemetry — a delayed data point degrades the dashboard, doesn't break it.
- **Board sketch:** the three v(t) curves side by side, deadline marked; under
  each, its node task.
- The model (§2.1, §4.1) — the variables the whole semester runs on: task τ_i,
  period **T_i**, computation time **C_i**, relative deadline **D_i** (often = T_i),
  activation/release time, start time, finishing time, **response time R_i**
  (finish − release; the star of week 7). **Jitter** = the variation of any of
  these across instances; the lab measures *finishing/period jitter* first.
- **Question for the room:** classify the node's five tasks (scenario table)
  before I show the answers. Sampling is the trap: it *feels* soft (just reading
  a sensor) but its jitter poisons the control math — it's hard.

> **Misconception to anticipate:** "jitter averages out." For a control loop the
> worst sample is the one that matters, and averages hide it. This is why every
> lab table in the course asks for *max*, not mean.

## Segment 2 — Latency anatomy
- Walk the chain for one flow pulse, left to right, naming each delay:
  1. **Event → interrupt request**: sensor edge, input synchronizer (~cycles).
  2. **Interrupt latency**: NVIC accepts it — on this Cortex-M4, exception
     entry is 12 cycles *if nothing blocks it*; sections with interrupts masked
     stretch this (that's why long `irq_lock`s are poison).
  3. **ISR body**: capture + set a flag (µs if disciplined).
  4. **Hand-off wait**: the flag sits there until the loop *comes around* — in a
     superloop this is bounded by the longest full pass, i.e. by the slowest
     task's worst day. This is the villain link.
  5. **Service + actuation**: the handler runs, the valve moves.
- Fixed links add *latency*; variable links add *jitter*. Links 1–3 wobble a
  little here, because the L4's ART cache means an instruction fetch costs 0 or 4
  wait states depending on history. So today's lab measures the baseline twice —
  cache on, then cache off — and the difference *is* links 1–3, isolated on one
  board. Whatever survives the subtraction is link 4, the villain.
- **Board sketch:** the chain as five boxes with a brace under each naming its
  delay; circle box 4. Buttazzo §2.4 catalogs the sources of unpredictability
  (DMA, caches, interrupts, syscalls) — preview only, week 9 returns to it.
- **Question for the room:** which link does the blocking `calib` command
  stretch, and by how much? (They measure the answer in an hour.)

## Segment 3 — Requirements you can measure (EARS)
- "The valve must respond quickly" cannot fail a test — so it isn't a
  requirement. EARS (Easy Approach to Requirements Syntax — Mavin et al., 2009,
  written at Rolls-Royce for jet-engine control) fixes the sentence shape:
  - **While** ⟨state⟩, the system shall ⟨response⟩ **within** ⟨deadline⟩.
  - **When** ⟨event⟩, the system shall ⟨response⟩ **within** ⟨deadline⟩.
- One condition, one response, one number — and an ID (`REQ-CTRL-01`) so every
  future measurement can cite it. EARS has five patterns; this course uses the
  two above (state-driven ≈ periodic tasks, event-driven ≈ aperiodic ones — the
  grammar mirrors the task model they just learned).
- Live rewrite on the board, class supplying the pieces:
  - Bad: "sampling must be fast and regular."
  - EARS: "While irrigating, the system shall sample pressure every 1 ms with
    jitter below ⟨X⟩ µs." (X = what the lab measures today — requirements and
    baselines are born together.)
- **Question for the room:** write the e-stop one. (Target: "When pressure
  exceeds the threshold, the system shall close the valve within 5 ms." They
  need exactly this in Task D.)

> **Misconception to anticipate:** "requirements are paperwork." Counter: in
> Task D they write 5–8 and from then on *every* piece of evidence cites one —
> that's what makes week 8's defense possible. (Do **not** say "RTM" — that name
> is week 8's reveal.)

## What about FreeRTOS?
Two minutes: nothing in this talk is Zephyr's — taxonomy, task model, latency
chain, and EARS apply identically under FreeRTOS or bare metal. The vocabulary is
the transferable asset.

## Bridge to the lab
They run the provided superloop and fill the baseline table: expect ~µs-level
jitter — until the blocking command turns it into ms. That number is the course
baseline; everything after week 2 is measured against it. The cache-off column is
the appetiser for week 3, where the whole chip changes at once.

## References
- Buttazzo, §1.3 and §2.1–2.3 (the week's reading); §2.4 skimmed, returns in wk 9.
- A. Mavin et al., "Easy Approach to Requirements Syntax (EARS)", *IEEE RE'09* —
  short and readable; the five patterns in §III.
- J. Yiu, *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors*, 3rd
  ed., ch. 8 — exception entry timing (the 12 cycles) and what can delay it.
- Zephyr docs, *Interrupts* — docs.zephyrproject.org/latest/kernel/services/interrupts/
- STM32L4 reference manual (RM0351), EXTI + NVIC chapters, and §3.3 for the ART
  accelerator's cache and prefetch bits — where the numbers come from when the
  analyzer asks.
