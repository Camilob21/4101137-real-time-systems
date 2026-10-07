# Week 1 — Bring-up: the team, the board, the toolchain
> - **Reading:** [READINGS.md](../READINGS.md), week 1
> - **Module:** 0
> - **Prerequisite:** [setup.md](setup.md) done at home.

**From:** Eng. Samuel Cifuentes (Senior Architect) — *"Welcome to the Control
Systems team. SoilSense already measures; now it has to **act**, and a valve that
closes late bursts hoses. Before we talk kernels: I want everyone compiling and
flashing without friction. This week's deliverable is a working environment."*

Today: form pairs, verify each member's environment, and run code on both starter
platforms (physical STM32C0116-DK and `native_sim`).

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Can the team iterate fast? | Build→flash→monitor cycle < 1 min, demonstrated |

## What you'll measure

No timing yet — this week you measure the *setup*:

| Check | ✓ |
|---|---|
| blinky runs on the pair's C0116-DK | |
| `hello_world` runs on `native_sim` | |
| Serial console open and echoing | |
| Team RET created from the template | |

## Tasks

### Task A — Cross-check the environment
- Each member builds and flashes blinky on the C0116-DK **from their own laptop**.
- `west build -p -b stm32c0116_dk zephyr/samples/basic/blinky && west flash`
- **Evidence:** blinking LED, one flash per member.

### Task B — Serial console
- Flash `zephyr/samples/hello_world` and open the serial monitor (115200 8N1).
- Change the message, rebuild, verify the full iteration cycle.
- **Evidence:** monitor screenshot with the modified message.

### Task C — Create the team RET
- Copy [templates/ret.md](../templates/ret.md) into your team repo; fill in the
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
| **Evidence** — screenshots + team repo with RET (30) | 30 |
| **Analysis** — correct initial task set in the RET: H/F/S types well assigned (30) | 30 |
