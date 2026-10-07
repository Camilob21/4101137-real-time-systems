# Week 13 — SoilSense Hub kickoff
> - **Reading:** [READINGS.md](../READINGS.md), week 13
> - **Module:** 6
> - Also covers the checkpoints (wks 14–15) and demo day (wk 16).

**From:** Eng. Samuel Cifuentes — *"The project starts. The Hub is one box with
three personalities: it controls the pumps (hard), serves a human (GUI), and moves
data (routing). You've already measured everything you need to design it — today
nobody codes: today you **decide**, in writing. A mixed-criticality system is
designed before typing, or debugged forever."* — Challenge details and
stakeholders in the [scenario](../PROJECT_SCENARIO.md).

## What gets decided today (the kickoff ADRs)

| ADR | The decision | The evidence behind it |
|---|---|---|
| **ADR-P1 — Linux vs. MCU partitioning** | What runs on the SBC and what would demand an MCU (S3) | Tails: wk 9 (µs, MCU) vs. wk 10 (RT Linux) |
| **ADR-P2 — Timing budget** | The Hub's task set with its `REQ-HUB-xx` (EARS, as in wk 2): H/F/S types, periods, deadlines, end-to-end sensor→valve budget | RET §1 task set + §4 RTA/CBS |
| **ADR-P3 — Isolation** | Policy + runtime/period + CPU + IRQs for the loop | Week 12's recipe (ADR-004), adapted |
| **ADR-P4 — Functional safety** | **Safe state** (failure ⇒ valve closed) + watchdog: who kicks, who bites, what happens on a bite | Scenario requirement; demonstrated at checkpoint 2 |

## Session tasks

### Task A — Architecture proposal
- Diagram of the box: processes/threads, scheduling policies, CPUs, and the
  critical data path (pressure sensor → interlock → valve) marked in red.
- **Evidence:** the diagram + the 4 draft ADRs defended before Samuel (in class).

### Task B — Checkpoint plan
- Declare *what number* each checkpoint will demonstrate (not "progress": a number).
- **Evidence:** both targets written in the RET, with their load condition.

## The three milestones

| Week | Milestone | Passes if… |
|---|---|---|
| 14 | **Checkpoint 1** | The Hub's hard loop meets deadlines under synthetic load (wk-12 protocol), misses = 0, table presented |
| 15 | **Checkpoint 2** | Real GUI + routing integrated; interference evidence + measured end-to-end budget; **the watchdog bites live** (the loop is killed and the valve closes on its own) |
| 16 | **Demo day** | Live demo + **final RET** + the Hub's timing-evidence report |

## Project rubric (100 pts)

| | pts |
|---|---|
| **Kickoff** — 4 ADRs defended, citing evidence, not opinion (20) | 20 |
| **Checkpoint 1** — numeric target met and measured with a declared protocol (15) | 15 |
| **Checkpoint 2** — real interference + e2e budget + fail-safe demonstrated (20) | 20 |
| **Demo day** — stable live demo (15) · final RET: task set, analysis, and evidence coherent end to end (25) · honest postmortem: what fell short and why (5) | 45 |
