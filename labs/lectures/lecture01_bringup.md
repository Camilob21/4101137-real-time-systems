# Week-1 talk — Recap: why real-time (40 min)

- **Precedes:** [lab01_bringup.md](../lab01_bringup.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. explain why a correct result at the wrong time is a wrong result, citing a real failure.
2. describe the course contract (GreenField, the RET, "show me the trace").
3. verify their toolchain builds both starter targets.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: the Patriot clock | correct code, 28 dead — time was the bug |
| 5–15 | Recap → convergence | digital systems + computation structures + control meet at *when* |
| 15–25 | What real-time is (and isn't) | predictable ≠ fast; the tail is the verdict |
| 25–32 | The course contract | GreenField, the RET, evidence culture, grading |
| 32–37 | The toolchain map | why Zephyr; where FreeRTOS lives in this course |
| 37–40 | Bridge to the lab | today's deliverable is a working environment |

## Segment 1 — The Patriot clock (hook)
- The facts (GAO report, and Buttazzo §1.2 retells it): Dhahran, Feb 25 1991. The
  Patriot's clock ticks every 0.1 s — but 0.1 is not exact in binary: stored in a
  24-bit register, the error is ~0.000000095 s *per tick*. After 100 hours of
  continuous operation: ~0.34 s of accumulated drift. A Scud closes at ~1,676 m/s
  → the range gate looked ~687 m away from the missile. No intercept; 28 soldiers
  died in the barracks.
- Twist the knife: every computation was *correct*. The tracking math, the
  ballistics — all right. The system failed in the dimension nobody was testing:
  **time**.
- Second story, 30 seconds: STS-1, April 10 1981 — the first Shuttle launch
  scrubbed because the backup flight computer couldn't sync with the primaries: a
  timing race in initialization with a 1-in-67 probability of landing wrong
  (Garman, *"The BUG heard 'round the world"*).
- **Question for the room:** was the Patriot bug a performance problem? Would a
  faster CPU have fixed it? (No — it met all its throughput requirements.)

## Segment 2 — Recap → convergence
- They already own the three pieces; name each in their language:
  - **Digital systems**: setup/hold times, FSMs, timing diagrams. The hardware
    people already sign timing contracts — a flip-flop that latches late is a
    *wrong value*. This course asks software to sign the same kind of contract.
  - **Computation structures**: registers, the memory map, the vector table,
    polling vs. interrupts on the STM32. They have *written* superloops — they
    just never measured one.
  - **Control systems**: a discrete controller is derived assuming a *constant*
    sampling period T_s. Every formula they used (discretization, stability
    margins) silently assumes the software delivers samples on time. Jitter is a
    disturbance their control course never modeled.
- **Board sketch:** three arrows (logic / architecture / control) converging on
  one word: *when*. Under it: "this course = making *when* a guarantee".

## Segment 3 — What real-time is (and isn't)
- Definition to write down (Buttazzo §1.1): a real-time system is one whose
  correctness depends not only on the *logical result* but on the *time* at which
  results are produced.
- Real-time ≠ fast. Real-time = the **worst case is bounded and proven**. A
  system averaging 2 µs with a rare 20 ms spike fails a 10 ms deadline; a system
  at a constant 8 ms passes. Fast average, fat tail: dead crops (or worse).
- **Board sketch:** two latency distributions, same mean; a vertical deadline
  line; one distribution's tail crosses it. Label the tail "what this course
  hunts".
- **Question for the room:** which one ships in a ventilator?

> **Misconception to anticipate:** "real-time means fast." Dismantle with the
> sketch: the deadline line doesn't care about the mean. Buzzword check:
> "real-time analytics" in web dashboards = low latency *usually*; here it means
> *provably, always*.

## Segment 4 — The course contract
- GreenField Technologies: they join as firmware engineers; the briefing is
  PROJECT_SCENARIO.md. SoilSense already senses; their team makes it *act* —
  and actuation has deadlines set by physics (a bursting hose doesn't negotiate).
- The RET (Timing Evidence Report) is the living deliverable: every timing claim
  cites a measurement. House rule, verbatim, on the board: **"show me the trace"**.
- Grading rhythm: weekly labs (rubrics in each guide), workshop week 8 (quiz +
  design review), final project weeks 13–16 (the Hub).

## Segment 5 — The toolchain map
- One toolchain the whole semester: Zephyr — `west` (build/flash), CMake,
  devicetree (hardware described as data; week 3 shows why that matters).
  Two boards: STM32C0116-DK now (lent), ESP32-S3 from week 3 (theirs).
  `native_sim` builds on the laptop for logic; never for timing numbers.
- FreeRTOS: appears every single week as the industry comparison — nothing to
  install, everything to compare. Week 9 is its dedicated session.

## Bridge to the lab
No timing today: the measured thing is the *setup* (blinky per member, serial
cycle, team RET created). If the environment works, the semester's iteration loop
is < 1 min — and that loop is what every future measurement stands on.

## References
- Buttazzo, *Hard Real-Time Computing Systems* 4th ed., §1.1–1.2 (the week's reading).
- GAO, *Patriot Missile Defense: Software Problem Led to System Failure at
  Dhahran*, GAO/IMTEC-92-26 (1992) — the primary source, 16 pages, free online.
- J. Garman, "The BUG heard 'round the world", *ACM SIGSOFT SEN* 6(5), 1981.
- Zephyr *Getting Started Guide* — docs.zephyrproject.org/latest/develop/getting_started/
- Optional wider view: Lee & Seshia, *Introduction to Embedded Systems*, ch. 1
  (free at leeseshia.org).
