# Real-Time Systems — UNAL 4101137

A course about **real-time behavior** — scheduling, latency, jitter, deadlines — using
an **ESP32-S3** and **Zephyr RTOS** as the vehicle, then **PREEMPT_RT Linux**. Taught at
the Universidad Nacional de Colombia, Sede Manizales. The goal isn't the framework:
it's understanding *when* code runs and how to guarantee it. What the theory (RMS/EDF,
response-time analysis, priority inversion, WCET) predicts is verified by measurement
at every stage. All course material is in English; classroom delivery is bilingual.

## Project — GreenField Technologies

Students join **GreenField Technologies**, a fictional agri-tech startup, as firmware
engineers on its new Control Systems team ([briefing](PROJECT_SCENARIO.md)). Its soil
sensors already ship; the team automates irrigation. One system is rebuilt as the
course climbs the stack:

1. **SoilSense Control** as the provided superloop (`firmware/superloop/`): run,
   instrumented and measured on the NUCLEO-L476RG, with the flash cache on and off,
   then ported to the ESP32-S3 with one devicetree overlay.
2. The same node **migrated to the Zephyr kernel**: flags → message queues, polled
   work → threads, ISR bottom halves → workqueues; measured against the superloop,
   analyzed for schedulability, and given its own core.
3. **SoilSense Hub** on PREEMPT_RT Linux: a mixed-criticality gateway whose hard pump
   loop must survive a GUI and data routing on the same box, linked to the nodes over
   **CAN**, with one deadline crossing MCU, bus and Linux.

Deliverables are engineering documents: ADRs and the **RET (Timing Evidence Report)**,
where every timing claim cites a measurement. Format: [SESSION_FORMAT.md](SESSION_FORMAT.md).

## Before you start

| You need | From |
|---|---|
| C on a microcontroller: registers, interrupts, the NUCLEO-L476RG | Computation Structures (4100901) |
| Timing diagrams, setup/hold, FSMs | Digital Systems |
| Discrete-time control: sampling period, PI controllers | Control Systems |

Setup, done at home before week 1: [labs/setup.md](labs/setup.md).

## You will be able to

1. Classify tasks as hard, firm or soft, and write timing requirements that a test can fail.
2. Measure latency and jitter with a logic analyzer and a scheduler trace, and account for what each instrument costs.
3. Migrate a superloop to an RTOS and justify it with an A/B on worst cases.
4. Decide schedulability with utilization tests and response-time analysis, blocking included.
5. Isolate a hard loop: on its own core under AMP, and on an isolated CPU under PREEMPT_RT with `SCHED_DEADLINE`.
6. Design a mixed-criticality system with an end-to-end deadline across an MCU, a CAN bus and Linux, and a safe state that a watchdog enforces.

## Schedule

14 weekly sessions (Wednesdays, 4–7 pm): a 40-minute talk, a 2-hour lab, then wrap-up.
Per-week readings, with what to skip: [READINGS.md](READINGS.md). Session guides:
[labs/](labs/README.md).

| Week | Talk | Lab | The RET gains |
|---|---|---|---|
| 1 | Why real-time: the recap that converges on *when* | Toolchain check, blinky on the NUCLEO and `native_sim` | Team, boards, initial task set |
| 2 | Taxonomy, task models, latency anatomy | The provided superloop on the NUCLEO: jitter baseline, cache on and off | EARS requirements; baseline |
| 3 | The scheduler: threads, priorities, preemption | Port to the S3 with one overlay; the first thread | Silicon comparison; `C_i` on the S3 |
| 4 | IPC: message queues, workqueues, ISR deferral | The full migration; A/B against the superloop | ADR-001; overhead; stack high-water marks |
| 5 | Tracing: seeing the scheduler | CTF trace of one preemption; the tracer's cost | Annotated trace; instrument per `C_i` |
| 6 | Schedulability: U, RM, EDF, RTA, priority inversion | Fig. 4.13 on the S3; inversion reproduced and fixed; `calib` and the e-stop fixed | ADR-002, ADR-005; tests and RTA with blocking. Problem Set out |
| 7 | — | **Workshop**: quiz + design review | RET v1, tagged |
| 8 | FreeRTOS, multicore, WCET | **Guided**: the node split across the two cores (AMP), kept for the project | ADR-003 draft; tail table; the inter-core hop |
| 9 | PREEMPT_RT: what it changes in the kernel | SBC bring-up; `cyclictest` stock vs. RT | Latency histograms; the Hub's task set |
| 10 | CBS → `SCHED_DEADLINE`; affinity, isolation, IRQ steering | FIFO vs. DEADLINE under a hog; the interference rig | CBS budget; ADR-004 |
| 11 | Mixed criticality, partitioning, safety | Project kickoff: architecture, ADRs and the agent's spec | ADR-P1–P4; ADR-P5 draft; the agent's spec |
| 12 | CAN: the bus as a scheduled resource | Checkpoint 1: hard loop under load; AMP node and CAN link up | ADR-P5 with the bus RTA; ADR-003 closed |
| 13 | — | Checkpoint 2: agent-built GUI + routing; e2e budget; the watchdog bites | End-to-end budget, measured; the agent's code against its spec |
| 14 | — | **Demo day** | Final RET |

## Assessment

| Component | Weight |
|---|---|
| Labs, weeks 1–10, each graded by its rubric (the week-7 workshop counts as one; week 8 is guided and feeds the project) | 30 % |
| Project, weeks 11–14: kickoff 20 · checkpoint 1 15 · checkpoint 2 20 · demo day 45 | 70 % |

## AI use

| Activity | AI |
|---|---|
| The workshop quiz and every defense in class | Not allowed: these show what each of you knows |
| Labs and the rest of the project: firmware, scripts, RET prose | Allowed, and declared in the RET: tool and what it did |
| The Hub's GUI and routing (weeks 11–13) | Required: an agent builds them from your spec, and the RET shows by measurement whether it met it |

Every measured value comes from your team's hardware. A number an AI wrote is not
evidence.

## Hardware and cost

Groups of 2–3 buy a **Control Kit**: ESP32-S3 DevKitC, 8-channel logic analyzer,
pump + flow sensor + servo as the plant, ILI9341 display (~$190–320k COP), and a
CAN transceiver (≈ US$2–5). From week 9, merged groups share a **Hub Kit**: a Raspberry Pi 4
with a CAN HAT. The NUCLEO-L476RG from the prerequisite courses covers weeks 1–2.
Parts and links: [BOM.md](BOM.md).

## Toolchain

Zephyr is pinned for the semester in [west.yml](west.yml) (Zephyr main of 2026-09-01,
SDK 1.0.1), so every laptop and CI build the same tree; it moves between semesters,
after the firmware builds and runs on the new revision. The Zephyr firmware also
builds and runs on `native_sim`, for work without a board. Every push builds all firmware and checks the documents
([.github/workflows/ci.yml](.github/workflows/ci.yml); locally:
[scripts/build_all.sh](scripts/build_all.sh)).

## References

- G. Buttazzo, *Hard Real-Time Computing Systems*, 4th ed., Springer, 2024
  ([link](https://link.springer.com/book/10.1007/978-3-031-45410-3); free through
  UNAL's SpringerLink subscription). The theory modules follow it; its Linux chapters
  anchor weeks 9–10 and the project.
- The official Zephyr documentation for practice; FreeRTOS docs for the weekly comparison.
- Optional, week 6: Lee & Seshia, *Introduction to Embedded Systems* (free at [leeseshia.org](https://leeseshia.org)).
- Week 12: Davis, Burns, Bril and Lukkien, "Controller Area Network (CAN) schedulability
  analysis: refuted, revisited and revised", *Real-Time Systems* 35, 2007.

## Repository layout

| Path | What it is |
|---|---|
| [labs/](labs/README.md) | Lab guides, talks (Marp decks in `presentations/`), SOPs |
| [firmware/](firmware/) | Course-authored reference apps: `superloop/` (week 2), `sampling_thread/` (week 3), `kernel/` (week 4 on), `amp_node/` (week 8 and the project) |
| [templates/](templates/) | Lab, talk, SOP and RET templates |
| [PROJECT_SCENARIO.md](PROJECT_SCENARIO.md) · [READINGS.md](READINGS.md) · [BOM.md](BOM.md) | The GreenField briefing, the reading guide, the parts list |

---

Maintained by Sam C · Universidad Nacional de Colombia, Sede Manizales.
