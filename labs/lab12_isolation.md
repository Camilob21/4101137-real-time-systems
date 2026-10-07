# Week 12 — Isolation and interference: the Hub's dress rehearsal
> - **Tech guide:** [SOP-10](sops/sop10_preempt_rt.md), §5
> - **Reading:** [READINGS.md](../READINGS.md), week 12
> - **Module:** 5
> - **Course content closes today** — what follows is the project.

**From:** Eng. Samuel Cifuentes — *"Last rehearsal before the project. The real Hub
will have a GUI rendering and telemetry arriving in bursts — I want the pump loop
armored against that by **design**: affinity, CPU isolation, and its DEADLINE
contract, all together. Build me the interference rig and show me the loop
unmoved. That rig is, literally, the project's checkpoint 2."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does the full isolation design work as a whole? | Loop + synthetic GUI + bursts, measured |
| **Edwin** | What exact configuration do I deploy in the field? | The recipe lands in the ADR, reproducible |

## What you'll measure

| Measurement (10 ms loop, ≥ 5 min each) | Misses | Max jitter (µs) |
|---|---|---|
| DEADLINE loop, shared CPUs, full interference | ____ | ____ |
| DEADLINE loop **+ affinity to an isolated CPU**, same interference | ____ | ____ |
| Same as above + IRQs moved off the isolated CPU | ____ | ____ |

Full interference = synthetic render load (`glxgears`/`stress-ng --vm`) + network
bursts (`iperf3` toward the SBC) — the Hub's GUI and routing, simulated.

## Tasks

### Task A — The loop's CPU
- Isolate a core (cmdline: `isolcpus=3 nohz_full=3 rcu_nocbs=3`, SOP-10) and pin
  the loop with `taskset -c 3` (or `sched_setaffinity`).
- **Evidence:** `cat /sys/devices/system/cpu/isolated` + the loop running there (`ps -o psr`).

### Task B — The interference rig
- Launch the full interference on the remaining CPUs. Run the table's three rows
  (no isolation / with isolation / with IRQs moved — `/proc/irq/*/smp_affinity`).
- **Evidence:** table + per-condition histograms.

### Task C — The deployment recipe
- Write the ADR: the Hub loop's complete configuration (policy + runtime/period +
  CPU + IRQs) as a reproducible list of commands/cmdline, with the why of each
  line citing a row of the table.
- **Evidence:** ADR-004 in the RET; another group must be able to replicate it in 10 min.

## What about FreeRTOS?

Affinity exists in FreeRTOS SMP (`vTaskCoreAffinitySet`) and isolation is "don't
put anything else on that core" — feasible because all the software is yours.
Linux needs `isolcpus` + contracts because the system runs software you don't own.
Same idea as week 9 (partitioning cuts tails), a more hostile ecosystem.

## Deliverables (RET)

- **§3 Week-12 evidence:** three-configuration table + histograms.
- **§2 ADR-004 — The Hub's RT configuration** (the full recipe, justified).

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — isolation verified (15) · full interference rig (25) | 40 |
| **Evidence** — three configurations with a constant protocol (30) | 30 |
| **Analysis** — ADR-004 reproducible, every line justified by a measurement (30) | 30 |
