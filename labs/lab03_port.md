# Week 3 — The S3 port and the first thread
> - **Reading:** [READINGS.md](../READINGS.md), week 3
> - **Module:** 2
> - **Firmware:** your week-2 `firmware/superloop/` (TASKs 1–3 filled in). Commit it before you start: today's first piece of evidence is a diff.

**From:** Eng. Samuel Cifuentes — *"Two pieces of news. One: production picked the
ESP32-S3 for the node — more memory, a radio, and two cores we'll use later. Two: I
saw the baseline with the blocking command; I'm authorizing a kernel evaluation.
First, move the superloop to the S3 **without rewriting it** — if we chose the
software platform well, that costs an overlay, not a porting effort. Then, the
first thread."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | What did changing silicon cost? | Changed lines: count them in the diff |
| **Gustavo** | Is the S3 "worse" for real time than the L476? | Same-code jitter comparison, two chips |

## What you'll measure

| Measurement | L476RG (wk 2) | S3 superloop | S3 + sampling thread |
|---|---|---|---|
| Max sampling jitter, ≥ 30 s | (copy) | ____ µs | ____ µs |
| Max sampling jitter, `calib` active | (copy) | ____ µs | ____ µs |
| `backlog_peak`, `calib` active | (copy) | ____ ticks | ____ ticks |
| `lat_peak_us` (tick → thread start, firmware's own count) | — | — | ____ µs |
| Max control period (`instr_ctrl`), `calib` active | — | ____ ms | ____ ms |

## Tasks

### Task A — The port (devicetree in action)

Nobody wrote the S3 pin map for you: that file *is* the port. Create
`firmware/superloop/boards/esp32s3_devkitc_esp32s3_procpu.overlay` — Zephyr picks
it up because its name is the build target with `/` replaced by `_`. Start from a
copy of `nucleo_l476rg.overlay` and take the S3 pins from the table in
[firmware/superloop/README.md](../firmware/superloop/README.md).

| In the Nucleo file | On the S3 |
|---|---|
| `&gpiob 3`, `&gpioa 8`, … (one node per port) | every pin lives on `&gpio0` |
| `led0` is the board's LD2, already aliased | no plain LED on the devkit: add a `gpio-leds` node `valve_out` on GPIO21 and alias `led0` to it |
| `&usart1`, `&pwm2`, `&pwm3` disabled | delete those lines — they are STM32 nodes and the S3 tree has no such labels |
| SSD1306 under `&i2c1` | under `&i2c0` (SDA GPIO1 / SCL GPIO2), which the S3 board leaves off: add `status = "okay";` |

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/superloop && west flash
```

The console is on the devkit's **UART** jack, not the USB one. Warning: the build
also succeeds *without* the overlay — every pin is optional in `main.c`, so the
node runs with no instrumentation and the analyzer shows flat lines. If yours
does, check the file name.

- Count the port: `git add -A && git diff --cached --stat`. How many lines, in
  which files, and how many of them are C?
- **Evidence:** the diff-stat + `status` answering on the S3.

### Task B — Two silicons, same code
- Repeat the week-2 protocol on the S3 (same duration, same conditions); fill in
  the *S3 superloop* column, including the control-period row.
- The idle max changed a lot between chips. Put `instr_tele` side by side on
  both captures: which hardware difference explains it? (Read how each chip's
  UART driver sends one character: `uart_stm32_poll_out` vs.
  `uart_esp32_poll_out` in `zephyr/drivers/serial/`.)
- The S3 runs at 240 MHz against the L476's 80 MHz, but executes from external
  SPI flash through a cache. Where in your RET do clock and cache show up, if not
  in the max? Two sentences for both answers.
- **Evidence:** comparison table + captures.

### Task C — The first thread

Only sampling moves. The tick ISR stops raising a flag and queues the release
time in a `k_msgq`; a thread blocks on that queue, samples, and every 10th sample
raises the flag the loop already knows how to serve for control. Everything else
stays in the superloop. Four edits to `main.c` and `prj.conf`:

**STEP 1 — make room above `main`.** `main` is a thread too, at priority 0 by
default, and priorities below 0 are cooperative. To put a preemptive thread above
it, move `main` down. Add to `prj.conf`:

```
CONFIG_MAIN_THREAD_PRIORITY=10
```

**STEP 2 — the ISR side.** Replace `ticks_pending`, `backlog_peak` and
`tick_isr` (keep `K_TIMER_DEFINE`) with:

```c
K_MSGQ_DEFINE(tick_q, sizeof(uint32_t), 8, 4);
static atomic_t backlog_peak; /* worst backlog seen — `status` reports it */
static atomic_t lat_peak_us;  /* worst release -> thread start */
static atomic_t control_pending;

static void tick_isr(struct k_timer *t)
{
	uint32_t released = k_cycle_get_32();

	k_msgq_put(&tick_q, &released, K_NO_WAIT);

	atomic_val_t backlog = k_msgq_num_used_get(&tick_q);

	if (backlog > atomic_get(&backlog_peak)) {
		atomic_set(&backlog_peak, backlog);
	}
}
```

**STEP 3 — the thread.** Paste above the `Bring-up + the loop` section:

```c
#define SAMPLING_PRIO  2
#define SAMPLING_STACK 1536

static void sampling_thread(void *p1, void *p2, void *p3)
{
	uint32_t released;
	int control_div = 0;

	while (1) {
		k_msgq_get(&tick_q, &released, K_FOREVER);

		atomic_val_t lat = k_cyc_to_us_floor32(k_cycle_get_32() - released);

		if (lat > atomic_get(&lat_peak_us)) {
			atomic_set(&lat_peak_us, lat);
		}

		task_sampling();
		if (++control_div >= CONTROL_EVERY) {
			control_div = 0;
			atomic_inc(&control_pending);
		}
	}
}
K_THREAD_DEFINE(sampling_tid, SAMPLING_STACK, sampling_thread, NULL, NULL, NULL,
		SAMPLING_PRIO, 0, 0);
```

**STEP 4 — the loop.** In `main`, delete `int control_div = 0;` and replace the
whole `if (atomic_get(&ticks_pending) > 0) { … }` block with:

```c
		if (atomic_get(&control_pending) > 0) {
			atomic_dec(&control_pending);
			task_control();
		}
```

Then add `lat_peak_us=%ld` to the `status` line in `console_handle`, with
`(long)atomic_get(&lat_peak_us)` as its argument. Build, flash, and check that
`status` still reports a moving pressure. The reference is in
[firmware/sampling_thread/](../firmware/sampling_thread/) — use it to unblock,
not to skip.

- Fill in the last column. Does `calib` still ruin sampling? And control?
- `pressure_mv`, `estop` and `setpoint_mv` are now written in one thread and read
  in another. Name who writes and who reads each one, and say in one sentence why
  today's code gets away with it. Week 7 answers it properly.
- **Evidence:** capture with `calib` active, sampling and control on the same
  screen + the filled column.

## What about FreeRTOS?

Task C would be `xTaskCreate(sample_task, "sample", stack, NULL, prio, NULL)`, the
ISR posting with `xQueueSendFromISR` and the task blocking in `xQueueReceive` —
different API, same concept (and FreeRTOS priorities count *up*). What FreeRTOS
does **not** have is Task A: without devicetree, moving from STM32 to ESP32 means
changing SDKs, not writing an overlay.

## Deliverables (RET)

- **§3 Week-3 evidence:** the three-column table, the silicon comparison, and the
  sampling-vs-control reading under `calib`.
- **§1:** `C_i` re-measured on the S3 (the task set's final platform).

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — port via overlay, no C touched (15) · sampling thread working (25) | 40 |
| **Evidence** — complete three-column table (20) · port diff-stat (10) | 30 |
| **Analysis** — L476 vs. S3 reading (10) · why sampling survives `calib` and control doesn't (15) · shared-state answer (5) | 30 |
