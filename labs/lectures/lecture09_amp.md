# Week-9 talk — FreeRTOS, multicore, and WCET (40 min)

- **Precedes:** [lab09_amp.md](../lab09_amp.md)
- **Audience:** students right before the lab.

This is FreeRTOS's dedicated session — the weekly aside becomes the headline.

## Objectives
By the end, the student can:

1. map the course's Zephyr APIs to FreeRTOS and argue when each kernel is the right call.
2. distinguish global from partitioned multicore scheduling and predict which helps the *tail*.
3. choose and defend a WCET estimation method.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: the customer demands FreeRTOS | what do you actually gain and lose? |
| 5–18 | FreeRTOS, honestly | API map, strengths, weaknesses, the verdict criterion |
| 18–28 | Multicore: global vs. partitioned | and what Zephyr-on-S3 really offers (AMP) |
| 28–35 | WCET | measurement vs. static analysis; high-water-mark + margin |
| 35–40 | Bridge to the lab | driver + two images + the tail table |

## Segment 1 — FreeRTOS, honestly
- Key idea: the most-shipped RTOS; every vendor SDK embeds it. API map on one
  slide: `K_THREAD_DEFINE`↔`xTaskCreate`, `k_msgq`↔`xQueue`, `k_mutex`↔PI mutex,
  `k_work`↔timer daemon — everything this course taught transfers. Strengths:
  tiny footprint, ubiquity, and *on this exact board* real SMP via ESP-IDF with
  per-task pinning. Weaknesses: no devicetree (portability = SDK change), no EDF,
  no CPU reservations, fewer built-in services.
- **Board sketch:** the API map table, built with the class shouting the right column.
- **Question for the room:** the verdict criterion — product = "this S3, both cores
  squeezed" vs. "a family across varied silicon". Which kernel for each?

## Segment 2 — Multicore: global vs. partitioned
- Key idea: global = one scheduler migrates tasks across cores (best average
  utilization, migration jitter, shared-cache interference); partitioned = tasks
  pinned per core, each core analyzed alone with everything from weeks 6–7.
  Zephyr's Xtensa port has no SMP, so today is partitioned *by construction*:
  AMP via sysbuild, one image per core, hard loop alone on APPCPU (no console
  there — GPIO is the instrument, as always).
- **Board sketch:** two boxes per model; under partitioned, write "RTA valid per
  core" — the theory survives intact.

> **Misconception to anticipate:** "two cores ⇒ twice the capacity" and "the second
> core improves my loop's speed." Averages barely move — what a dedicated core buys
> is the *tail*: the rare spike from sharing is gone. The lab's table row 4 exists
> to force this reading.

## Segment 3 — WCET
- Key idea: three routes — static analysis (sound, needs a cache model, explodes on
  the S3's flash cache), pure measurement (cheap, can miss the worst path), and the
  industry default: high-water mark under stress + engineering margin. The RET's
  C_i column is route three; today's stress thread is what makes the high-water
  mark honest.
- **Question for the room:** why is static WCET *easier* on the C0116 than on the
  S3? (Week 3's jitter answer, resurfacing: caches.)

## Bridge to the lab
Two builds: the flow sensor becomes a real driver behind a devicetree binding, and
sysbuild produces two images. Then the three-case table — expect the maxima, not
the averages, to tell the story; ADR-003 must cite the cost too (two images, no
APPCPU console). Problem Set 2 is due today.
