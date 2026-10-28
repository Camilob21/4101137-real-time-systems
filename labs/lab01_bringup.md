# Week 1 — Bring-up: the team, the board, the toolchain
> - **Talk:** [01_why_real_time](presentations/01_why_real_time.md)
> - **Reading:** [READINGS.md](../READINGS.md), week 1
> - **Module:** 0
> - **Prerequisite:** [setup.md](setup.md) done at home.

**From:** Eng. Samuel Cifuentes (Senior Architect) — *"Welcome to the Control
Systems team. SoilSense already measures; now it has to **act**, and a valve that
closes late bursts hoses. Before we talk kernels: I want everyone compiling and
flashing without friction. This week's deliverable is a working environment."*

Today: form pairs, verify each member's environment, and run code on both starter
platforms: the NUCLEO-L476RG from the prerequisite courses, and `native_sim`.

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Can the team iterate fast? | Build→flash→monitor cycle < 1 min, demonstrated |

## What you'll measure

This week the timing under test is your own iteration loop. Hand in the prediction
column before the lab.

| Quantity | Prediction | Your value | Target |
|---|---|---|---|
| Edit → build → flash → message on the console, one member's laptop | ____ s | ____ s | < 60 s |
| Same, incremental build (one line changed, no `-p`) | ____ s | ____ s | |
| Members with blinky running from their own laptop | | ____ / ____ | all |

## Tasks

### Task A — Cross-check the environment
- Each member builds and flashes blinky on the NUCLEO-L476RG **from their own laptop**.
- From `~/rts`: `west build -p -b nucleo_l476rg zephyr/samples/basic/blinky && west flash`
- **Evidence:** blinking LED, one flash per member.

### Task B — Serial console
- Flash `zephyr/samples/hello_world` and open the serial monitor (115200 8N1).
- Change the message, rebuild, verify the full iteration cycle. Time it twice: once
  with `-p` (pristine) and once without; fill in the table.
- **Evidence:** monitor screenshot with the modified message + both times.

### Task C — Create the team RET
- Copy [templates/ret.md](../templates/ret.md) into your fork (setup §2); fill in the
  header and the control-loop row with the values from the
  [scenario](../PROJECT_SCENARIO.md) (period 10 ms; `C_i` stays `____` until measured).
- **Evidence:** link to the team repo with the RET under version control.

## What about FreeRTOS?

There is no `west`/devicetree equivalent: each silicon comes with its vendor SDK
(ESP-IDF, STM32Cube, nRF Connect) and FreeRTOS ships embedded inside it. That's the
trade-off we'll keep measuring: Zephyr pays its learning curve once and travels
across chips; FreeRTOS is quick to learn but the environment changes with every vendor.

## Deliverables (RET)

- **Header + §1:** team, boards, initial Control task set (from the talk and the
  scenario), all `C_i` as `____`.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — blinky per member (20) · full serial cycle (20) | 40 |
| **Evidence** — screenshots, both cycle times + team repo with RET (30) | 30 |
| **Analysis** — correct initial task set in the RET: H/F/S types well assigned (30) | 30 |
