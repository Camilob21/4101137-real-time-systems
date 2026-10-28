# Reading Guide — Buttazzo, *Hard Real-Time Computing Systems* (4th ed.)

Course reference: Giorgio Buttazzo, *Hard Real-Time Computing Systems*, 4th ed.,
Springer, 2024 (available via SpringerLink/SINAB).

**General rule: read statements, examples, and figures; skip the proofs.** The
book fences every derivation inside explicit *Proof* blocks — most of the book's
math is the author *proving* the results, not using them. In this course the labs
replace the proofs: where the book proves a theorem, you verify it with the logic
analyzer and the traces. The math that does get used (the math of the
timing-evidence reports) fits in about ten formulas and two short algorithms —
listed at the end.

## Reading by week

| Week | Module | Read | Skip | Note |
|------|--------|------|------|------|
| 1 | 0 | §1.1–1.2 | — | Closes the recap (digital systems → computation structures → control): what real time is; the Shuttle and Patriot stories are the course's argument |
| 2 | 1 | §1.3, §2.1–2.3 | §2.4 (picked up again in week 8) | The semester's vocabulary: task models, constraint types, sources of unpredictability (DMA, cache, interrupts, syscalls) |
| 3 | 2 | §10.1–10.3 | §10.4–10.5 (implementation detail) | Anatomy of an RT kernel: states, ready queues, context switch — Zephyr as the living example |
| 4 | 2 | §10.6–10.7 | CAB implementation (§10.6.2) | Compare CABs with Zephyr's message queues; §10.7: kernel overhead exists and gets measured (A/B against the week-2 baseline) |
| 5 | 4 | §13.5.1; §1.3 (reread with measurement eyes) | — | The book is thin on *how* to measure; the tracing lab covers that |
| 6 | 3 | §4.1–4.4 (statements, tables, and examples), §4.5.1–4.5.2 (RTA), §4.7; EDF optimality statement (§3.3.1); §7.1–7.3, PIP rules (§7.6.1) and PCP rules (§7.7.1), statement of Theo. 7.2 | The U_lub derivations (§4.3.2–4.3.3, ~7 pages of calculus), proofs of Theo. 4.1 and 4.2; the rest of ch. 3; §4.5.3–4.5.4; the lemma chain of §7.6.2, exact blocking computation (§7.6.3), §7.8 (SRP) | The Fig. 4.13 example (RM fails, EDF doesn't, at U = 0.97) and the priority inversion are reproduced in the lab on the S3. RTA is a 15-line algorithm (Fig. 4.17), not a theorem: the homework implements it in Python with the measured C_i and B. **Problem Set**: exercises from chs. 2, 4 and 7 + RTA (solutions in ch. 14; due at the workshop). Optional (free PDF): Lee & Seshia, *Introduction to Embedded Systems*, ch. 2 — feedback control, for the jitter-vs-control stretch |
| 7 | 3 | Review: chs. 2, 4, and 7 | — | **Workshop** — ch. 14 has solutions to the exercises of chs. 1–9 for practice |
| 8 | 4 | §13.1–13.2 (RTOS landscape); §13.5 (WCET tools); §2.4 | — | FreeRTOS is **not in the book** — it's the comparison talk (reference: official FreeRTOS docs). Ch. 13 gives the landscape: many kernels, one theory. There's no multiprocessor chapter: §2.4 is the hook; the lab uses **Zephyr AMP** (one image per core) = *partitioned* scheduling, measured. WCET: measurement vs. static analysis vs. high-water-mark + margin |
| 9 | 5 | §13.3.4–13.3.5 (PREEMPT_RT, SCHED_DEADLINE) | — | What PREEMPT_RT changes inside the kernel; SBC bring-up and `cyclictest` |
| 10 | 5 | §6.9.1–6.9.4 (CBS); §9.3 (the resource-reservation idea); **all of ch. 12**; §13.1.1 (RT-POSIX) | Rest of chs. 5–6 (the other servers: one intuition slide is enough); §6.9.5–6.9.6 | The CBS is 3 pseudocode rules (Fig. 6.15) plus two one-line results: isolation (U_s = Q_s/T_s no matter what) and R_i ≈ C_i/U_s. That *is* SCHED_DEADLINE. Ch. 12 has almost no math: it's C code (pthread + the ptask library), and the lab follows it nearly verbatim |
| 11 | 6 | Ch. 11: §11.2 (from requirements to timing constraints), §11.3, §11.5.2 (mixed criticality) | — | The robot's task table in §11.4 (periods, WCETs, hard/soft) mirrors the SoilSense Control task set. Functional-safety vocabulary (not in the book): watchdog, safe state, IEC 61508 / DO-178C |
| 12 | 6 | Davis, Burns, Bril and Lukkien, "CAN schedulability analysis: refuted, revisited and revised" (*Real-Time Systems* 35, 2007): the system model, the frame-time formula and the sufficient test | The proofs and the exact busy-period analysis | Not in the book. CAN arbitration is fixed-priority scheduling without preemption: the week-6 RTA with a blocking term, on a bus |
| 13–14 | 6 | — | — | No new reading; chs. 11–12 as working references for the project |

## The math that does get used

These are the formulas and algorithms that appear in the deliverables (the
schedulability analysis of the timing-evidence reports):

- Periodic task model: `a_{i,j} = Φ_i + (j−1)T_i`, `d_{i,j} = a_{i,j} + D_i` (§4.5).
- Utilization factor: `U = Σ C_i/T_i` (§4.1.1).
- RM test (Liu & Layland): `U ≤ n(2^{1/n} − 1)` — the result and Table 4.2 (§4.3.3).
- Hyperbolic test (less pessimistic): `∏(U_i + 1) ≤ 2` (Theo. 4.1).
- EDF test: `U ≤ 1`, necessary and sufficient (Theo. 4.2).
- RTA recurrence: `R_i = C_i + Σ_{h<i} ⌈R_i/T_h⌉ C_h`, iterated to a fixed point
  (Fig. 4.17) — implemented as a script.
- Blocking bound under PIP: at most `min(l_i, s_i)` critical sections; `B_i` = sum
  of the longest ones (Theo. 7.2); the extended RTA uses `R_i = C_i + B_i + interference`.
- CBS/SCHED_DEADLINE: bandwidth `U_s = Q_s/T_s` (isolation, Theo. 6.8) and
  response time `R_i ≈ C_i/U_s` (§6.9.6).
- CAN frame time, 11-bit IDs, worst-case bit stuffing: `C_m = (55 + 10 s_m) τ_bit`
  for `s_m` data bytes (135 bit times for 8 bytes; τ_bit = 2 µs at 500 kbit/s).
- CAN response time, sufficient test (Davis et al. 2007): `R_m = J_m + w_m + C_m`
  with `w_m = B_max + Σ_{k∈hp(m)} ⌈(w_m + J_k + τ_bit)/T_k⌉ C_k`, iterated like the
  RTA; `B_max` is the longest frame on the bus (a frame already on the wire can't
  be preempted).

Everything else — ch. 4's calculus minimizations, ch. 7's lemma chains, the server
analyses of chs. 5–6, ch. 8, and nearly all of ch. 9 — is out of the course's scope.
