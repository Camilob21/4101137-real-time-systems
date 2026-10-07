# Week-3 talk — The scheduler: threads, priorities, preemption (40 min)

- **Precedes:** [lab03_port.md](../lab03_port.md)
- **Audience:** students right before the lab.

## Objectives
By the end, the student can:

1. explain what a devicetree overlay buys in a port.
2. describe the RT-kernel anatomy (thread states, ready queue, context switch).
3. map the superloop's polled sampling to a thread + message queue.

## Structure
| Min | Segment | Purpose in one line |
|---|---|---|
| 0–5 | Hook: two pieces of news | production picked the S3; the kernel evaluation is authorized |
| 5–15 | The port: hardware as data | devicetree/overlay — why the C doesn't change |
| 15–27 | Anatomy of an RT kernel | states, ready queue, preemption, switch cost (§10.1–10.3) |
| 27–33 | The first mapping | polled sampling → thread + `k_msgq` |
| 33–37 | What about FreeRTOS? | same scheduler model, no devicetree |
| 37–40 | Bridge to the lab | the diff-stat and the new jitter |

## Segment 1 — The port: hardware as data
- The idea: the application names hardware by *role*; a separate description
  binds the role to pins. Vocabulary on the board, one line each:
  - **Node**: a device in the tree (`&adc1`, an LED).
  - **Property**: its facts (`gpios = <&gpioa 1 ...>`).
  - **Binding**: the schema saying what properties a `solomon,ssd1306` needs.
  - **Alias / chosen**: role names (`led0`, `zephyr,console`) the app looks up.
  - **Overlay**: a patch on the board's tree — *this* is the port.
- In Zephyr the tree is compiled: `DEVICE_DT_GET(...)` resolves at build time,
  costs zero RAM at runtime (unlike Linux, where the same idea — same syntax,
  they'll see it again in week 10's SBC — is parsed at boot).
- Today's proof: the lab's Task A — students write
  `boards/esp32s3_devkitc_esp32s3_procpu.overlay` themselves from the Nucleo one:
  every pin moves to `&gpio0`, the valve gets its own node, the STM32-only
  nodes go. `main.c` diff: **zero lines**. Warn them: without the overlay the
  build still succeeds, because every pin is optional — flat lines on the
  analyzer mean a misnamed file.
- **Board sketch:** one `main.c` box fed by two small DT files (Nucleo pins /
  S3 pins); arrow labels "port = data, not code".
- **Question for the room:** week 1's toolchain map said vendor SDKs embed
  FreeRTOS — what does *this* port cost there? (SDK change; the FreeRTOS segment
  closes the loop.)

## Segment 2 — Anatomy of an RT kernel
- What a kernel fundamentally adds (Buttazzo §10.1–10.3): the CPU stops being
  "whatever the loop reaches next" and becomes a *managed resource*.
- **A thread is**: a stack + saved registers + a TCB (priority, state). Nothing
  mystical — the superloop had one implicit thread; now there are several, each
  owning its own "where was I".
- **States**, drawn as the lifecycle diagram: *ready* (wants CPU), *running*
  (has it), *blocked/pending* (waiting on time or data — costs zero CPU). The
  superloop's crime in this language: it has no *blocked* state — everything is
  always "running", burning passes polling flags.
- **The scheduler's one rule**: the highest-priority *ready* thread runs.
  Always. Enforced at every **preemption point**: an ISR ends, a mutex unlocks,
  a sleep expires. "Immediately" replaces "when the loop comes around" — link 4
  of last week's chain gets a new, bounded name.
- **The context switch**: save registers to the old stack, restore from the new.
  On the L476 (Cortex-M) it rides the PendSV exception — Yiu ch. 10 shows the
  exact sequence. The S3's Xtensa LX7 has no PendSV and 64 windowed registers:
  Zephyr's `arch_switch` spills the live windows to the stack instead. Same idea,
  different cost — on the order of a µs, measured, not believed, in week 4's
  Task C.
- **Priorities in Zephyr**: lower number = more important; negative priorities
  are *cooperative* (won't be preempted — the course leaves them alone until the
  tracing week shows one).
- **`main` is a thread too**, at priority 0 by default — the most important
  preemptive level. A superloop `main` never blocks, so a new thread at 0 or
  below never runs at all. Hence the lab's first step:
  `CONFIG_MAIN_THREAD_PRIORITY=10`, and sampling at 2.
- **Board sketch:** the three-state diagram; next to it, last week's five-link
  chain with link 4 crossed out and replaced by "preempt: bounded by switch cost".
- **Question for the room:** what should the blocking `calib` command do to a
  *higher-priority* sampling thread? (Nothing — that's this afternoon's
  measurement. Let them commit to the prediction out loud.)

> **Misconception to anticipate:** "the kernel adds overhead, so it's slower."
> Slower on average by µs of switching — but the *worst case* stops depending on
> the longest loop body. The A/B in week 4 shows both effects in one table.

## Segment 3 — The first mapping
- Migration is mechanical, one piece at a time — today only sampling:
  - The ISR stops setting a flag and posts the release time to a **`k_msgq`**.
  - `K_THREAD_DEFINE(sampling_tid, STACK, sampling_thread, ..., 2, 0, 0)` blocks
    on `k_msgq_get` — the polled wait becomes a wake-up, and the timestamp lets
    the thread measure its own release latency (`lat_peak_us`).
  - Every 10th sample the thread raises the old flag for control, which stays in
    the loop.
- Everything else stays superloop. Mixed systems are normal mid-migration — that
  is *how* real products migrate.
- **Question for the room:** control still lives in the loop. What will `calib`
  do to it this afternoon? (It still stalls — the lab measures it next to
  sampling, and week 4 finishes the job.)
- **Board sketch:** first row of the mapping table (flag+poll → ISR+`k_msgq`+
  thread). The full table is week 4's talk.

## What about FreeRTOS?
`xTaskCreate` ↔ `K_THREAD_DEFINE`, `xQueueSend/Receive` ↔ `k_msgq_put/get` —
same preemptive fixed-priority model, near-1:1 API (one habit flip: FreeRTOS
priorities go *up*, Zephyr's go down). What has no equivalent is Segment 1:
moving STM32 → ESP32 under FreeRTOS means changing vendor SDKs, not writing
one overlay.

## Bridge to the lab
Two numbers to predict before touching anything: the port's `git diff --stat`
(expect ~0 lines of C) and the S3's idle max jitter against the L476's ≈ 6 ms.
Let them bet on clock vs. flash cache. *For you:* neither wins — the S3's UART
has a 128-byte TX FIFO, so the 1 Hz telemetry line is queued in ≈ 80 µs instead
of blocking ≈ 6 ms on the L476's one-byte USART. Clock and cache show up in the
`C_i` widths, not the max. `calib` is time-based, so it costs ≈ 400 ms on both.

## References
- Buttazzo, §10.1–10.3 (the week's reading; §10.4–10.5 skipped — implementation
  detail).
- Zephyr docs: *Threads* and *Scheduling* —
  docs.zephyrproject.org/latest/kernel/services/threads/ — the state diagram and
  the cooperative/preemptive split; *Introduction to devicetree* —
  docs.zephyrproject.org/latest/build/dts/intro.html
- J. Yiu, *The Definitive Guide to ARM Cortex-M3 and Cortex-M4 Processors*, 3rd
  ed., ch. 10 — PendSV and the context-switch sequence, register by register.
- FreeRTOS kernel docs, *Task states* — freertos.org/RTOS-task-states.html (the
  same lifecycle diagram, for the comparison slide).
