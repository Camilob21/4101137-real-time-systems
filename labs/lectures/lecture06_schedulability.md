# Week-6 talk — Schedulability: utilization bounds, RM/DM, EDF (40 min)

- **Precedes:** [lab06_schedulability.md](../lab06_schedulability.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. compute U and apply the Liu & Layland and hyperbolic tests.
2. explain why RM can miss below U = 1 while EDF meets exactly up to U = 1.
3. connect scheduling jitter to control-loop degradation.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: Daniela's two sensors | "does it fit?" deserves math, not vibes |
| 5–17 | Utilization and the RM tests | U, the 69 % bound, hyperbolic, the gray zone |
| 17–28 | EDF and Fig. 4.13 | dynamic priorities buy exactness; the famous miss |
| 28–33 | Jitter meets control | why the loop degrades before it misses |
| 33–37 | What about FreeRTOS? | fixed priorities only — design to pass RM |
| 37–40 | Bridge to the lab | reproduce 4.13 on our board; inject jitter |

## Segment 1 — Utilization and the RM tests
- Key idea: U = ΣC_i/T_i with *measured* C_i is the load; the tests are verdicts on
  it. Liu & Layland: U ≤ n(2^{1/n}−1) → ~69 % guaranteed under RM. Hyperbolic:
  ∏(U_i+1) ≤ 2, same idea, less pessimistic. Both are *sufficient*: failing them
  proves nothing yet.
- **Board sketch:** the number line 0 → 1 with the 0.69 mark and the gray zone up
  to 1 labeled "RM: maybe — check case by case (RTA, next week)".
- **Question for the room:** the node's U with Daniela's sensors lands at 0.85 —
  what can you *not* conclude from Liu & Layland?

> **Misconception to anticipate:** "U < 1 means it's schedulable." Only under EDF.
> Under RM, 0.97 can fail — they'll watch it fail this afternoon.

## Segment 2 — EDF and Fig. 4.13
- Key idea: EDF reorders by *urgency* (earliest absolute deadline), and its test is
  exact: U ≤ 1, full stop. Walk Fig. 4.13: same task set at U = 0.97 — RM's fixed
  priorities waste the critical instant, EDF doesn't. This is the one figure the
  course reproduces on silicon.
- **Board sketch:** the two timelines from the figure, the RM miss circled.
- **Question for the room:** if EDF is optimal, why does industry mostly ship RM?
  (Hold the answer — it's the FreeRTOS segment.)

## Segment 3 — Jitter meets control
- Key idea: a control loop assumes its sampling period; jitter is a disturbance the
  controller never modeled. Before a deadline ever misses, the loop's error grows.
  "Meets deadlines" and "controls well" are different bars — Daniela cares about
  the second.
- **Board sketch:** flow setpoint vs. actual under 0 / 2 / 5 ms of injected jitter.

## What about FreeRTOS?
No EDF in the kernel — fixed priorities only (same for most shipped RTOSes; the
answer to Segment 2's question: simplicity and inertia). The professional move
under FreeRTOS at U = 0.97 is redesign until RM passes. That constraint is why the
book spends half a chapter on RM.

## Bridge to the lab
Two experiments: Fig. 4.13 live (RM misses, flip to EDF, it meets — two captures)
and the jitter-injection rig on the flow loop. Problem Set 1 goes out today; the
math from this talk is exactly the math it drills.
