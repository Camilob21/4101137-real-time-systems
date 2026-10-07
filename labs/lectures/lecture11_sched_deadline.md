# Week-11 talk — Servers, reservation, CBS → SCHED_DEADLINE (40 min)

- **Precedes:** [lab11_sched_deadline.md](../lab11_sched_deadline.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. explain why fixed priorities fail once third-party software shares the CPU.
2. state the CBS in its three rules and its isolation guarantee U_s = Q_s/T_s.
3. translate a measured loop into a `SCHED_DEADLINE` runtime/period contract with margin.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: the hog at priority 95 | one integration mistake starves the pump loop |
| 5–15 | Why priorities stop being enough | your guarantee currently rests on everyone else's discipline |
| 15–27 | Reservation and the CBS | a CPU contract: Q_s every T_s, no matter what |
| 27–33 | SCHED_DEADLINE in practice | sched_setattr, admission control |
| 33–37 | What about FreeRTOS? | no equivalent — and why that's fine on an MCU |
| 37–40 | Bridge to the lab | starve it, then contract it |

## Segment 1 — Why priorities stop being enough
- Key idea: a priority is a *relative* claim — it guarantees nothing about how much
  CPU you get, only that you beat whoever's below. On the node that was fine: we
  reviewed every task. The Hub runs a GUI toolkit and a network stack we didn't
  write; one process at FIFO 95 (a typo, an installer default) and the loop at 90
  silently gets zero CPU. Forever.
- **Board sketch:** two FIFO bars, 95 eclipsing 90 — no misbehavior, just arithmetic.
- **Question for the room:** whose code review protects you here? (Nobody's —
  that's the point.)

## Segment 2 — Reservation and the CBS
- Key idea: flip the model — instead of ranking tasks, *reserve* CPU: the
  Constant Bandwidth Server grants budget Q_s every period T_s. Three rules
  (Fig. 6.15): consume budget while running; budget exhausted → deadline pushed,
  task demoted till recharge; recharge every period. Two one-line consequences:
  isolation — the server gets U_s = Q_s/T_s *regardless of what else runs* — and
  R_i ≈ C_i/U_s inside the reservation. That's the theory; `SCHED_DEADLINE` is its
  kernel implementation (CBS + EDF among servers).
- **Board sketch:** the budget sawtooth over three periods, one of them with a hog
  hammering the other core of the diagram — the sawtooth doesn't care.

> **Misconception to anticipate:** "DEADLINE is just a very high priority." It's a
> contract, and it binds *you* too: exhaust your runtime and the kernel throttles
> your own loop until recharge. Undersizing Q_s hurts you, not the neighbors —
> hence the lab's margin question.

## Segment 3 — SCHED_DEADLINE in practice
- Key idea: `sched_setattr` with runtime ≤ deadline ≤ period; the kernel runs
  admission control and *refuses* contracts that oversubscribe (ΣU_s bounded) — the
  scheduler doing week 6's schedulability test at syscall time.
- **Question for the room:** the loop measured C ≈ 1.1 ms per 10 ms period — what
  runtime do you request, and what's your argument for the cushion?

## What about FreeRTOS?
No reservations in FreeRTOS or Zephyr — priorities only. Defensible on an MCU: all
the code is yours, review replaces contracts. The moment third-party code shares
the CPU, that defense dies — which is precisely why the Hub is Linux and why this
mechanism lives there.

## Bridge to the lab
Ch. 12's ptask pattern nearly verbatim: build the periodic loop, starve it under a
FIFO hog (row 2 — capture the freeze), then sign the DEADLINE contract and watch
the same hog become irrelevant (row 3, misses = 0). The two sentences connecting
runtime/period to U_s = Q_s/T_s go straight into the RET.
