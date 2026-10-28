# Week 10 — SCHED_DEADLINE and isolation: the Hub's dress rehearsal
> - **Talk:** [10_deadline_isolation](presentations/10_deadline_isolation.md)
> - **Tech guide:** [SOP-09](sops/sop09_preempt_rt.md), §5
> - **Reading:** [READINGS.md](../READINGS.md), week 10
> - **Module:** 5
> - **Course content closes today** — what follows is the project.

**From:** Eng. Samuel Cifuentes — *"On the MCU, priorities were enough because we
controlled every line of code. On the Hub we don't: the GUI and the routing are
software we didn't write. I need the pump loop to have its CPU **guaranteed by
contract**, no matter what runs next to it, and armored by **design** against a
GUI rendering and telemetry arriving in bursts: contract, affinity, isolation, all
together. Build me the interference rig and show me the loop unmoved. That rig is,
literally, the project's checkpoint 2."*

The periodic task follows the book's ch. 12 almost to the letter (pthread + the
ptask pattern).

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does the loop keep its period even if a neighbor goes rogue? | Misses under FIFO vs. DEADLINE with a hog on the loop's core |
| **Edward** | Can a compromised process starve the loop? | With DEADLINE, the contract forbids it: demonstrated |
| **Edwin** | What exact configuration do I deploy in the field? | The recipe, in ADR-004, reproducible |

## What you'll measure

Hand in the prediction column before the lab. Every row: the 10 ms loop, ≥ 5 min.

| Configuration | Predicted misses / max jitter (µs) | Misses | Max jitter (µs) |
|---|---|---|---|
| 1. `SCHED_FIFO` 90 on core 3, quiet | ____ / ____ | ____ | ____ |
| 2. + a FIFO 95 **hog on core 3** | ____ / ____ | ____ | ____ |
| 3. `SCHED_DEADLINE` 2 ms / 10 ms on core 3 + the same hog | ____ / ____ | ____ | ____ |
| 4. `SCHED_DEADLINE` on the shared cores 0–2, full interference | ____ / ____ | ____ | ____ |
| 5. `SCHED_DEADLINE` on isolated core 3, the same interference | ____ / ____ | ____ | ____ |
| 6. Row 5 + IRQs moved off core 3 | ____ / ____ | ____ | ____ |

Full interference = a synthetic render load (`stress-ng --vm 2`) + network bursts
(`iperf3` toward the SBC) on cores 0–2: the Hub's GUI and routing, simulated.

## Tasks

### Task A — The periodic task, on an isolated core
- Before the lab, isolate core 3 (SOP-09 §5: `isolcpus=3 nohz_full=3 rcu_nocbs=3`,
  one reboot). Nothing lands there unless you put it there.
- Implement the pump loop as a periodic pthread with
  `clock_nanosleep(TIMER_ABSTIME)` and a miss counter: the book's ptask pattern
  (§12, code given). Instrument it with an SBC GPIO; the analyzer is still the judge.
- **Evidence:** `cat /sys/devices/system/cpu/isolated`, the loop on core 3
  (`ps -o psr`), misses = 0 on a quiet system (row 1).

### Task B — Priorities aren't enough, contracts are
- Pin a busy-loop to the loop's core at FIFO 95: `taskset -c 3 chrt -f 95 ./hog`,
  a misassigned priority, a realistic integration mistake. Row 2: the loop starves.
- Same task, now `SCHED_DEADLINE` (runtime 2 ms, deadline = period = 10 ms), the
  same hog beside it. Set the affinity before the policy: `taskset -c 3 chrt -d …`
  (SOP-09 §5). Row 3.
- **Evidence:** the capture of the frozen GPIO, the miss counts, and two sentences:
  runtime/period is the CBS's `U_s = Q_s/T_s`, the isolation the book promises,
  observed.

### Task C — The interference rig
- Start the full interference on cores 0–2. Run rows 4–6: the DEADLINE loop on the
  shared cores, then on core 3, then with the IRQs moved off it
  (`/proc/irq/*/smp_affinity_list`).
- **Evidence:** the table + a histogram per row.

## Homework, due at the kickoff

**ADR-004, the deployment recipe:** the Hub loop's complete configuration (policy +
runtime/period + CPU + IRQs + governor) as a list of commands and cmdline
parameters, the why of each line citing a row of the table. Another group must be
able to replay it in 10 minutes.

## What about FreeRTOS?

No equivalent of the contract: FreeRTOS (and Zephyr) give you priorities, not CPU
reservations. Affinity exists in FreeRTOS SMP (`vTaskCoreAffinitySet`), and
isolation there means "put nothing else on that core", which works because every
task is yours. Linux needs a contract and four isolation layers because the box
runs software you don't own.

## Deliverables (RET)

- **§3 Week-10 evidence:** the six-row table, captures of rows 2–3, histograms of rows 4–6.
- **§4:** the Hub loop's budget as a CBS: the chosen `U_s` and its margin (Task A's
  measured runtime + a justified cushion).
- **§2 ADR-004 — The Hub's RT configuration:** the recipe, every line justified.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — ptask loop on the isolated core (10) · starvation reproduced (10) · DEADLINE isolating (10) · full interference rig (10) | 40 |
| **Evidence** — six rows with a constant protocol (20) · captures and histograms (10) | 30 |
| **Analysis** — CBS↔`SCHED_DEADLINE` in their own words, with a justified `U_s` (15) · ADR-004 reproducible, every line justified by a row (15) | 30 |
