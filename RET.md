# RET — Timing Evidence Report

- **Team:** Anderson Kaleth Ángel Orozco · <nombre completo del compañero(a)>
- **Boards:** ESP32-S3-DevKitC-1 <N16R8 / N8R2> "S3-A" (MAC `<xx:xx:xx:xx:xx:xx>`) <· segunda placa "S3-B" (MAC ...) si la hay>. Weeks 1–2 run on the ESP32-S3 instead of the NUCLEO-L476RG (the team has no NUCLEO; external LED on GPIO21 as `led0`). `native_sim/native/64` for logic only, never for timing.
- **AI use:**
  - Week 1: Claude (Anthropic) — step-by-step lab guide, the `lab01/ciclo.py` timing script and a first draft of this header and §1. Every measured value comes from our hardware.

**Living document** — updated every week; handed in at the workshop (week 7) and
at the close (week 14).

**House rule:** *"show me the trace"* — every timing claim cites a measurement.

## 1. The system and its task set

Requirements first — one sentence each, EARS style (*when/while `<condition>`, the
system shall `<response>` within `<deadline>`*) — then the task that implements them:

| ID | Requirement |
|---|---|
| REQ-CTRL-01 | While the system is irrigating, the control loop shall run every 10 ms (deadline = period). |
| REQ-CTRL-02 | When pressure exceeds the overpressure threshold, the system shall close the valve within 5 ms. |
| REQ-SAMP-01 | While the system is running, the system shall sample the pressure and flow sensors every 1 ms (1 kHz), each sample completed within its own period. |
| REQ-CONS-01 | When an operator command arrives on the console, the system shall answer within 1 s; a later answer is discarded. |
| REQ-TELE-01 | While the system is running, the system shall send one telemetry line to the Hub every 1 s; a late line degrades the dashboard but breaks nothing. |

| Task | Req. | Type (H/F/S) | Period | Deadline | Measured C_i | How it was measured |
|---|---|---|---|---|---|---|
| Control loop (PI → valve PWM) | REQ-CTRL-01 | Hard | 10 ms | = T (10 ms) | ____ | ____ (planned: GPIO toggle + AD2 logic analyzer) |
| Sensor sampling | REQ-SAMP-01 | Hard | 1 ms (1 kHz) | = T (1 ms) | ____ | ____ |
| Overpressure e-stop | REQ-CTRL-02 | Hard | sporadic (event) | 5 ms | ____ | ____ |
| Command console | REQ-CONS-01 | Firm | sporadic (on command) | 1 s | ____ | ____ |
| Telemetry to the Hub | REQ-TELE-01 | Soft | 1 s | = T (1 s) | ____ | ____ |

Why each type:

- **Hard (control, sampling, e-stop):** a miss can cause physical damage. A late control step or a late e-stop lets pressure build until a hose bursts; a late sample hands the controller a wrong sampling period (jitter acts as a disturbance).
- **Firm (console):** a late answer is worthless, since the operator has moved on, but harmless to the plant.
- **Soft (telemetry):** a late line still has value; it only degrades the dashboard.

## 2. ADRs

### ADR-001 — `<title>`
**Context:** … · **Decision:** … · **Justification (with numbers):** … · **Status:** …

## 3. Evidence by week

Each entry cites the `REQ`(s) it verifies.

### Week 1 — iteration loop (ESP32-S3, laptop of <nombre>)

No REQ yet: this verifies the team's tooling, not the product.

| Quantity | Prediction | Measured | Target |
|---|---|---|---|
| Edit → build → flash → message on the console, pristine (`-p`) | ____ s | ____ s | < 60 s |
| Same, incremental build (one line changed, no `-p`) | ____ s | ____ s | |
| Members with blinky running from their own laptop | | ____ / 2 | all |

Instrument: `lab01/ciclo.py`, the host's monotonic clock from Enter until the text arrives on the UART console (115200 8N1), one run each. Reading: <una frase: qué fase domina cada ciclo y si se cumplió el objetivo>.

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