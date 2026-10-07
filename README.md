# Real-Time Systems — UNAL 4101137

A course about **real-time behavior** — scheduling, latency, jitter, deadlines — using
an **ESP32-S3** and **Zephyr RTOS** as the vehicle. Taught at the Universidad Nacional
de Colombia, Sede Manizales. The goal isn't the framework — it's understanding *when*
code runs and how to guarantee it: what the theory (RMS/EDF, response-time analysis,
priority inversion, WCET) predicts, verified by measurement at every stage.

Zephyr gives the course one toolchain (`west`, CMake, Kconfig) and **devicetree**
as the hardware-description language — the same syntax students later meet again in
the Linux kernel. Its portability also gives every lab a no-hardware path
(`native_sim`, Renode).

Everything lives in this repository — session guides, instructor material, and the
**course-authored reference firmware** students run, study, and migrate.

## Project scenario — GreenField Technologies

The course is **project-oriented**: students work inside a realistic product scenario
rather than doing isolated assignments (see
[PROJECT_SCENARIO.md](PROJECT_SCENARIO.md)). They join **GreenField Technologies** —
a fictional agri-tech startup — as **Firmware Engineers on the new Control Systems
team**. GreenField's sensing product (SoilSense, a soil-monitoring mesh) already
shipped; monitoring alone doesn't close the loop, so the next product line is
automated irrigation:

- **SoilSense Control** — an ESP32-S3 real-time irrigation controller: a flow/pressure
  control loop with a **hard** deadline, periodic sensor sampling, **soft** telemetry,
  and a **firm** command console. This is the node the course builds and rebuilds.
- **SoilSense Hub** — a Linux SBC gateway with **hard real-time duties of its own**:
  it runs the pump station's control loop and safety interlock *while also* serving a
  local touchscreen **GUI** and routing telemetry between Control nodes and the cloud.
  A mixed-criticality box — the final project (weeks 13–16) is proving the hard loop
  survives the GUI and routing load.

The briefing is self-contained. Deliverables are professional engineering documents:
ADRs and design records, extended here with **timing evidence** (schedulability
analysis + measured latency/jitter tables).

## Through-line

The one system — **SoilSense Control** — is rebuilt as the course climbs the stack:

1. first as the **provided superloop** (`firmware/superloop/`, course-authored) —
   single Zephyr main thread plus ISRs — which
   students run as their Zephyr get-started, then instrument and measure on the
   NUCLEO-L476RG as the baseline — first as shipped, then with the flash cache and
   prefetch switched off, which isolates microarchitectural jitter on one board,
   one variable — then port to the ESP32-S3 with one devicetree overlay and
   re-measure (same code, two chips);
2. then **migrated to the Zephyr kernel** — a guided mapping of each superloop piece
   to its kernel counterpart: flags → message queues, polled work → threads, ISR
   bottom halves → workqueues — measured again against that baseline;
3. finally **one level up on embedded Linux** (PREEMPT_RT, `SCHED_DEADLINE`), closing
   with the **SoilSense Hub**: a mixed-criticality gateway whose hard control loop
   must coexist with a GUI and data routing on the same box — where real-time
   *design* (priority/deadline assignment, CPU isolation, Linux-vs-MCU partitioning)
   is the deliverable, not just working code.

The node's tasks embody the deadline taxonomy the course teaches — labeled in the
spec and verified in the traces. All course material is in English; classroom delivery is bilingual.

## Repository layout

| Path | What it is |
|---|---|
| [labs/](labs/) | One lab guide per session, plus `lectures/` (instructor scripts) and `sops/` (bring-up mechanics) — format in [SESSION_FORMAT.md](SESSION_FORMAT.md) |
| [firmware/](firmware/) | **Course-authored reference apps.** `superloop/` is the get-started: students run it in week 2, it gets explained in the talk, and module 2 is its guided migration to kernel threads. `sampling_thread/` is the week-3 reference (S3 overlay + first thread), `kernel/` the week-4 one (full migration). More stages land as the semester climbs |
| [templates/](templates/) | lab / lecture / SOP / RET templates |
| [PROJECT_SCENARIO.md](PROJECT_SCENARIO.md) · [READINGS.md](READINGS.md) · [BOM.md](BOM.md) | The GreenField briefing, the per-week reading guide, and the parts list |

## Modules (logical units within this repo)

| # | Module | What it covers |
|---|--------|----------------|
| 0 | Setup & recap | **Pre-course setup guide** (done at home, verified week 1) + prerequisite recap bridging digital systems, computation structures, and control into *why real-time*; `west`, devicetree at a glance, `native_sim`/Renode fallbacks |
| 1 | Superloop baseline | Real-time taxonomy (hard/firm/soft) and latency anatomy; students **run and study the provided superloop** (`firmware/superloop/`, main thread + ISRs) and measure its jitter as the course baseline on the NUCLEO-L476RG — the board they already own from the prerequisite courses — first with its flash cache as shipped, then switched off |
| 2 | Zephyr kernel fundamentals | Opens with the port: the provided superloop rebuilt for the ESP32-S3 with one devicetree overlay, baseline re-measured (two chips compared). Then the **guided migration** superloop → threads, message queues, workqueues, ISR deferral — the talk maps each superloop piece to its kernel counterpart; jitter measured against the S3 baseline |
| 3 | Workshop — scheduling & timing | RMS/EDF schedulability, response-time analysis, WCET estimation; priority inversion reproduced and fixed live (Zephyr mutexes do priority inheritance) |
| 4 | Instrumented measurement | Two sessions bracketing the theory module: tracing (SystemView/CTF) at week 5 — so the schedulability labs verify by trace — then WCET methodology, a Zephyr driver with its devicetree binding, and multicore at week 9: partitioned scheduling via **Zephyr AMP** (sysbuild, one image per core), with global/SMP as the talk contrast. Week 9's talk is also FreeRTOS's dedicated slot |
| 5 | Embedded Linux real-time | Three sessions (weeks 10–12) on a PREEMPT_RT Linux SBC: `cyclictest`, servers/CBS → `SCHED_FIFO`/`SCHED_DEADLINE` (Buttazzo's Linux chapters, incl. the ch. 12 pthread/ptask lab); larger groups sharing boards |
| 6 | Final project — SoilSense Hub | Mixed-criticality gateway: hard control loop + safety interlock sharing a PREEMPT_RT SBC with a GUI and data routing. Deliverables: partitioning ADR, priority/deadline/CPU-isolation design, watchdog + defined fail-safe state, interference evidence |

## Semester schedule

16 weekly sessions (Wednesdays, 4–7 pm). Each session runs as a **40-minute talk +
2-hour lab**, with the remaining time for wrap-up and Q&A. The on-ramp is compressed
so the kernel starts at week 3: a **pre-course setup guide** (module 0) is done at
home and verified in week 1, whose talk bridges the prerequisites — digital systems,
computation structures, control — into *why real-time*; week 2 opens with a quick
recap of that conclusion. The tracing session runs at week 5, *before* the theory
module, so the schedulability labs verify by trace. Content closes at week 12;
weeks 13–16 belong to the final project. Per-week readings from the course text are
in **[READINGS.md](READINGS.md)**, including which sections — and which
proofs — to skip.

| Week | Module | Talk (40 min) | Lab (2 h) |
|------|--------|---------------|-----------|
| 1 | 0 | Recap: digital systems → computation structures → control systems — converging on *why real-time*; course overview | Toolchain check (pre-course setup guide done at home), first build; blink on the NUCLEO-L476RG and `native_sim` |
| 2 | 1 | Quick RT recap, then the vocabulary: taxonomy (hard/firm/soft), task models, latency anatomy (interrupt → activation → jitter) | Run the provided superloop (`firmware/superloop/`) on the NUCLEO-L476RG as the Zephyr get-started; walk the code, instrument it, measure the jitter baseline table, then re-measure with the flash cache off |
| 3 | 2 | The scheduler: threads, priorities, preemption | Port the provided superloop to the ESP32-S3 (one devicetree overlay — Zephyr portability, demonstrated); re-measure the baseline, compare silicon; begin the guided migration to threads |
| 4 | 2 | IPC: message queues, workqueues, ISR deferral | Complete the threaded node; A/B measurement against the week-3 S3 baseline |
| 5 | 5 | Instrumented measurement: Zephyr tracing (SystemView/CTF), latency/jitter/CPU load | Trace the threaded node; quantify kernel overhead vs. the baseline |
| 6 | 3 | Schedulability: utilization bounds, RM/DM, EDF — and what jitter does to a control loop | Implement and analyze a periodic task set; verify the math in traces; induce jitter in the flow loop and measure the control degradation. Problem set 1 out (ch. 2, 4; due at the workshop) |
| 7 | 3 | Response-time analysis; priority inversion, PI/PC protocols | Reproduce inversion, fix with PI mutex. Problem set 2 out (ch. 7 + RTA; due week 9) |
| 8 | 3 | Synthesis and Q&A | **Workshop**: schedulability analysis of the Control task set + quiz |
| 9 | 4 | FreeRTOS, the industry alternative: API mapping from Zephyr, where it's strong and weak (talk only — nothing to install); multicore: global vs. partitioned; WCET: measurement vs. static analysis, high-water-mark + margin | Driver with DT binding; **Zephyr AMP lab** on the S3 (sysbuild, two images: APPCPU runs the hard loop, PROCPU runs the load) — cross-core jitter tail measured with the logic analyzer |
| 10 | 5 | PREEMPT_RT: what it changes in the kernel | Linux SBC bring-up (shared per group); `cyclictest` latency |
| 11 | 5 | Aperiodic servers, overload & resource reservation, CBS → `SCHED_DEADLINE` | Periodic tasks under Linux: `SCHED_FIFO` vs. `SCHED_DEADLINE` (Buttazzo ch. 12 pthread/ptask lab, part 1) |
| 12 | 5 | Linux RT in practice: affinity, CPU isolation, priorities for mixed loads | ch. 12 lab completed; interference measurement under load; content closes |
| 13 | 6 | SoilSense Hub kickoff: mixed criticality, Linux-vs-MCU partitioning; safety vocabulary — watchdogs, fail-safe states, IEC 61508 / DO-178C | Proposal + architecture ADRs: what runs where, priorities/deadlines, CPU isolation plan, fail-safe design |
| 14 | 6 | — | Checkpoint 1: Hub's hard control loop meets deadlines under synthetic load |
| 15 | 6 | — | Checkpoint 2: GUI + data routing integrated; interference evidence + end-to-end deadline budget |
| 16 | 6 | — | **Demo day**: live demos + timing-evidence reports |

## Hardware & tooling

NUCLEO-L476RG (weeks 1–2 baseline; already owned from the prerequisite courses) · ESP32-S3 devkit ·
Zephyr (`west`, CMake, devicetree, Kconfig) · VS Code ·
`native_sim` / Renode for no-hardware paths ·
Zephyr tracing (SystemView/CTF) · a PREEMPT_RT Linux SBC (e.g. Raspberry Pi) for
modules 5–6, shared per group. Students buy components in groups of 2–3 — see the
**[BOM](BOM.md)** (pump + flow sensor + servo as the plant, ILI9341 touch display,
logic analyzer for jitter measurement; ~$190–320k COP per group).

## Reference

**Giorgio Buttazzo — *Hard Real-Time Computing Systems: Predictable Scheduling
Algorithms and Applications*, 4th ed., Springer, 2024**
([link.springer.com/book/10.1007/978-3-031-45410-3](https://link.springer.com/book/10.1007/978-3-031-45410-3)).
The course's theory modules (schedulability, RMS/EDF, response-time analysis,
resource-access protocols, aperiodic servers/CBS) follow this text — it covers soft
real-time as well as hard, and its Linux chapters anchor module 5 and the final
project; the labs validate its predictions by measurement. Likely available to
students at no cost through UNAL's SpringerLink subscription (SINAB). For practice,
the primary reference is the official Zephyr documentation (FreeRTOS docs back the
comparison talks). The week-by-week reading guide — theorem statements over proofs; the labs supply the
evidence — is in [READINGS.md](READINGS.md).

For the control-loop session (week 6), the free **Lee & Seshia, *Introduction to
Embedded Systems*** ([leeseshia.org](https://leeseshia.org)) is optional reading.

## What it demonstrates

Real-time engineering taught through a single product measured at every stage — the
same node as a superloop, multithreaded on Zephyr, and scaled to PREEMPT_RT Linux,
with FreeRTOS as the running industry comparison — and the scheduling theory tied to
observed latency and jitter rather than slides. The ESP32-S3 is the teaching instrument; the lasting takeaway is knowing
*when* your code runs.

---

Maintained by Sam C · Universidad Nacional de Colombia, Sede Manizales.
