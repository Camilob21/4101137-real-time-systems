# RET — Timing Evidence Report

- **Team:** `<names>`
- **Boards:** `<serials/nicknames>`
- **AI use:** `<per week: tool, and what it did>`

**Living document** — updated every week; handed in at the workshop (week 7) and
at the close (week 14).

**House rule:** *"show me the trace"* — every timing claim cites a measurement.

## 1. The system and its task set

Requirements first — one sentence each, EARS style (*when/while `<condition>`, the
system shall `<response>` within `<deadline>`*) — then the task that implements them:

| ID | Requirement |
|---|---|
| REQ-CTRL-01 | While the system is irrigating, the control loop shall run every 10 ms (deadline = period). |

| Task | Req. | Type (H/F/S) | Period | Deadline | Measured C_i | How it was measured |
|---|---|---|---|---|---|---|
| Control loop | REQ-CTRL-01 | Hard | 10 ms | = T | ____ | <GPIO + analyzer / trace> |

## 2. ADRs

### ADR-001 — `<title>`
**Context:** … · **Decision:** … · **Justification (with numbers):** … · **Status:** …

## 3. Evidence by week

Each entry cites the `REQ`(s) it verifies.

### Week 2 — superloop baseline (state the board)
<jitter/latency table + a one-sentence reading>

### Week 3 — S3 baseline and silicon comparison
…

## 4. Schedulability analysis

U = ΣC_i/T_i with **measured** C_i; test used (RM / hyperbolic / EDF); RTA as a
script with its output; blocking B_i if there are mutexes. (Formulas: READINGS.md,
"The math that does get used".)

From week 12: the CAN frame plan (IDs, periods, sizes), bus utilization and each
frame's response time; then the end-to-end budget of each requirement that crosses
the bus, hop by hop:

| Requirement | Node `R` (APPCPU) | IPM hop | CAN `R` | Hub wake-up (max) | Actuation | Sum | Deadline | Measured end to end |
|---|---|---|---|---|---|---|---|---|
| e-stop → pump stop | ____ | ____ | ____ | ____ | ____ | ____ | 20 ms | ____ |

## 5. Functional safety (final project)

Declared safe state (failure ⇒ valve closed), watchdog, and the evidence of the
fail-safe firing.

## 6. Agent-built components (final project)

The Hub's GUI and routing, built by an agent from `spec/hub-soft.md`. Tool, model
and where the session log lives: `<…>`.

| REQ | What the spec asks | How it was measured | Measured | Met? |
|---|---|---|---|---|
| REQ-HUB-xx | … | … | ____ | ____ |

Deviations: where the agent's code departed from the spec, and which measurement
caught it.
