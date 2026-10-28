# Week 11 — SoilSense Hub kickoff
> - **Talk:** [11_kickoff](presentations/11_kickoff.md)
> - **Reading:** [READINGS.md](../READINGS.md), week 11
> - **Module:** 6
> - Also covers the checkpoints (wks 12–13) and demo day (wk 14).
> - **Tech guide:** [SOP-12](sops/sop12_can.md) — the CAN link between the node and the Hub.

**From:** Eng. Samuel Cifuentes — *"The project starts. The Hub is one box with
three personalities: it controls the pumps (hard), serves a human (GUI), and moves
data (routing). You've already measured everything you need to design it — today
nobody codes: today you **decide**, in writing. A mixed-criticality system is
designed before typing, or debugged forever."* — Challenge details and
stakeholders in the [scenario](../PROJECT_SCENARIO.md).

## What gets decided today (the kickoff ADRs)

| ADR | The decision | The evidence behind it |
|---|---|---|
| **ADR-P1 — Linux vs. MCU partitioning** | What runs on the SBC and what would demand an MCU (S3) | Tails: wk 8 (µs, MCU) vs. wk 9 (RT Linux) |
| **ADR-P2 — Timing budget** | The Hub's task set with its `REQ-HUB-xx` (EARS, as in wk 2): H/F/S types, periods, deadlines; the end-to-end e-stop budget (node trips on APPCPU → IPM → PROCPU → CAN frame → Hub stops the pump, ≤ 20 ms) split into its hops | RET §1 task set + §4 RTA/CBS |
| **ADR-P3 — Isolation** | Policy + runtime/period + CPU + IRQs for the loop | Week 10's recipe (ADR-004), adapted |
| **ADR-P4 — Functional safety** | **Safe state** (failure ⇒ valve closed) + watchdog: who kicks, who bites, what happens on a bite | Scenario requirement; demonstrated at checkpoint 2 |
| **ADR-P5 — The bus** *(drafted today, closed at checkpoint 1)* | CAN frame plan: IDs in deadline order, periods, payload sizes; bus utilization and each frame's worst-case response | Week-12 talk: CAN response-time analysis |

## Session tasks

### Task A — Architecture proposal
- Diagram of the box: processes/threads, scheduling policies, CPUs, the CAN link to
  the nodes, and the critical paths marked in red (pressure sensor → interlock →
  valve; node e-stop → IPM → CAN → pump stop).
- **Evidence:** the diagram + the 4 draft ADRs (and the ADR-P5 draft) defended
  before Samuel (in class).

### Task B — Checkpoint plan
- Declare *what number* each checkpoint will demonstrate (not "progress": a number).
- **Evidence:** both targets written in the RET, with their load condition.

### Task C — The spec for the agent
- Nobody on the team types the GUI or the routing: an AI agent builds them from
  your spec. Write it as `spec/hub-soft.md` in the team repo:
  1. Their `REQ-HUB-xx` in EARS, each with its type (F/S) and a number a test can fail.
  2. The budget they live in: the policy and CPUs they may use (core 3 is the loop's, ADR-P3).
  3. The interfaces they may touch (the ADR-P5 frames, the loop's status) and the ones they may not.
  4. For each requirement, the measurement that decides it.
- Any agent is fine; declare the tool and keep the session log (RET §6).
- **Evidence:** the spec in the repo, defended with the ADRs.

## The three milestones

| Week | Milestone | Passes if… |
|---|---|---|
| 12 | **Checkpoint 1** | The Hub's hard loop meets deadlines under synthetic load (wk-10 protocol), misses = 0, table presented; the node runs its week-8 AMP split (ADR-003 closed); the CAN link carries node telemetry and the e-stop frame (SOP-12); ADR-P5 closed with the bus RTA |
| 13 | **Checkpoint 2** | The agent-built GUI + routing integrated and measured against `spec/hub-soft.md`; interference evidence + the e-stop → pump-stop path measured end to end against its 20 ms; **the watchdog bites live** (the loop is killed and the valve closes on its own) |
| 14 | **Demo day** | Live demo + **final RET** + the Hub's timing-evidence report |

## Project rubric (100 pts)

| | pts |
|---|---|
| **Kickoff** — 4 ADRs defended, citing evidence, not opinion (15) · the agent spec: every requirement testable, budget and interfaces stated (5) | 20 |
| **Checkpoint 1** — numeric target met and measured with a declared protocol (10) · AMP node, CAN link + bus RTA (5) | 15 |
| **Checkpoint 2** — agent-built GUI + routing measured against their spec, under real interference (5) · e2e budget across the bus, measured (10) · fail-safe demonstrated (5) | 20 |
| **Demo day** — stable live demo (15) · final RET: task set, analysis, and evidence coherent end to end (25) · honest postmortem: what fell short and why, and where the agent departed from the spec and which measurement caught it (5) | 45 |
