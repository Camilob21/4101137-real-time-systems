# Week 8 — Workshop — the design review
> - **Reading:** review of chs. 2, 4, and 7 — ch. 14 has practice solutions.
> - **Module:** 3
> - **Due today:** Problem Set 1.
> - **Workshop scope:** chs. 2, 4, 7 + everything measured through week 7.

**From:** Eng. Samuel Cifuentes — *"Formal design review. Each pair presents the
complete analysis of their node: task set, utilization, RTA with blocking, and the
evidence backing it. It's the same exercise you'll do your whole career under
another name: design review. The quiz is individual — I need to know that **both**
of you know."*

## Session format (3 h)

| Time | Activity |
|---|---|
| 0:00–0:40 | **Individual quiz** (theory from chs. 2, 4, 7 — problem-set style) |
| 0:40–2:30 | **Workshop**: each pair completes and defends its analysis (below) |
| 2:30–3:00 | Cross-review: each pair audits another pair's RET against the rubric |

## The analysis to defend (RET up front)

1. **Task set** (§1): the Control node's five tasks, measured `C_i` and their instrument.
2. **Utilization** (§4): U, applicable test (RM/hyperbolic/EDF), and verdict.
3. **RTA** (§4): script, per-task output, `R_i ≤ D_i` — including the mutex's `B_i`.
4. **Evidence** (§3): every `REQ` in §1 reaches a capture or trace in two hops
   (requirement → task → measurement).
5. **Surprise question**: Samuel changes a parameter (a period, a `C_i`) live —
   the pair re-runs the script and re-reads the verdict in minutes, not days.

> **The industry name**: the requirement → task → analysis → evidence chain you're
> about to defend is called an **RTM** (*Requirements Traceability Matrix*). You've
> been maintaining one since week 2; today it just gets its résumé name.

## Deliverables

- Individual quiz (in class).
- **RET frozen as v1** (tag `workshop` in the team repo) with §1–§4 complete.
- Problem Set 1 solved (handed in at the start). Problem Set 2 continues (week 9).

## Rubric (100 workshop pts)

| | pts |
|---|---|
| **Individual quiz** — theory, chs. 2, 4, 7 | 40 |
| **Defended analysis** — task set + U + RTA correct and consistent with the evidence (30) · response to the live change (10) | 40 |
| **RET v1** — complete, versioned, evidence linked (15) · cross-audit done with judgment (5) | 20 |
