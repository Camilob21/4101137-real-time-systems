# Week-13 talk — Mixed criticality, partitioning, and safety (40 min)

- **Precedes:** [lab13_kickoff.md](../lab13_kickoff.md)
- **Audience:** students right before the kickoff.

## Objectives
By the end, the student can:

1. define a mixed-criticality system and argue a Linux-vs-MCU partition with measured tails.
2. specify a safe state and a watchdog chain (who kicks, who bites, what a bite does).
3. state what IEC 61508 and DO-178C regulate, in one sentence each.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: one box, three personalities | design it now, or debug it forever |
| 5–17 | Mixed criticality and the partitioning ADR | what would force an MCU — answered with tails |
| 17–29 | Safety vocabulary | safe state, watchdog chain, fail-safe demonstrated |
| 29–34 | The standards, briefly | IEC 61508, DO-178C — what they regulate and why they exist |
| 34–40 | How the project runs | ADR defense today; checkpoints are numbers |

## Segment 1 — Mixed criticality and the partitioning ADR
- Key idea: hard (pump loop, interlock), firm/soft (GUI, routing) sharing one
  computer — the defining risk is the low-criticality load hurting the
  high-criticality tail. The design question (ADR-P1): what stays in Linux, what
  would force an MCU? Not answered by taste but by the two numbers already in their
  RETs: week 9's µs tails (MCU) vs. week 10/12's tens-of-µs (RT Linux, isolated) —
  against each requirement's deadline.
- **Board sketch:** the Hub box split into criticality bands, the wk-9/wk-12 tail
  numbers written next to each band's deadline.
- **Question for the room:** which Hub requirement, if its deadline were 100 µs
  instead of 10 ms, would flip the partition? (That's the ADR's sensitivity.)

## Segment 2 — Safety vocabulary
- Key idea: a real-time guarantee covers the system *working*; safety covers it
  *failing*. Safe state: declared, reachable without software (failure ⇒ valve
  closed — spring-return, not a hope). Watchdog chain: who kicks (the loop, only
  after a healthy cycle), who bites (hardware timer), what the bite does (drive to
  safe state, then maybe reboot). Checkpoint 2 kills the loop live and the valve
  must close on its own.
- **Board sketch:** the kick-and-bite loop; cross out the kick and follow the arrows
  to the closed valve.

> **Misconception to anticipate:** "the watchdog is a debug/reset convenience."
> It's a safety actuator — the *last* control loop. Kicking it from a timer ISR
> (which keeps running while the app is dead) is the classic way to neuter it;
> Samuel will look for exactly that in ADR-P4.

## Segment 3 — The standards, briefly
- Key idea: two names they'll meet in job posts. IEC 61508: functional safety for
  electrical/electronic systems — hazard → SIL level → required rigor (the
  ventilator/industrial world). DO-178C: software in airborne systems — evidence
  and traceability by criticality level (the avionics world). One shared spine:
  requirements traced to evidence — the RTM they've kept since week 2 is the
  entry-level version of both.

## Segment 4 — How the project runs
- Key idea: today nobody codes — four ADRs defended against the evidence in their
  own RETs; checkpoint targets declared as *numbers* with load conditions, not
  "progress". Weeks 14–15 checkpoints, week 16 demo day: live demo + final RET +
  honest postmortem (the 5 rubric points for admitting what fell short).

## Bridge to the lab
The kickoff session is the lab: architecture diagram with the critical path in red,
the four draft ADRs defended before Samuel, checkpoint numbers in the RET. The
kernel comparison retires undefeated: ADR-P1's MCU option can be Zephyr or FreeRTOS
— the partitioning argument is kernel-agnostic.
