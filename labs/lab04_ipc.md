# Week 4 — The full migration and the A/B
> - **Reading:** [READINGS.md](../READINGS.md), week 4
> - **Module:** 2
> - **Firmware:** your week-3 `firmware/superloop/` (S3 overlay + sampling thread) is the starting point. The A side of today's A/B is the *S3 superloop* column you measured in week 3.

**From:** Eng. Samuel Cifuentes — *"Finish the migration and bring me the A/B: superloop vs. kernel, same tasks, same board, same conditions. That table decides the product architecture — and I'm the one defending it to Gustavo, so I want to be able to cite it without embarrassment. And one more thing: threads bring context switches, but they also bring stack overflows. Measure your high-water marks before we ship this."*

Today the talk's mapping is completed: every piece of the superloop finds its
kernel counterpart.

| Superloop piece | Kernel counterpart |
|---|---|
| ISR flag + check in the loop | Short ISR + `k_msgq` (it carries data) or `k_sem` (it only says "go") |
| Heavy polled work | Thread with its own priority |
| Improvised "bottom half" in the loop | `k_work` on a workqueue of your own |
| Console that blocks everything | Console thread at the lowest priority, sleeping between polls |

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does the kernel improve the worst case, not just the average? | A/B with maxima, not averages |
| **Gustavo** | What did we buy with the new complexity? | The blocking command no longer breaks anything — measured |

## What you'll measure

| Measurement (S3) | S3 superloop (wk 3) | Kernel (today) |
|---|---|---|
| Max sampling jitter | (copy) | ____ µs |
| Max sampling jitter with `calib` | (copy) | ____ µs |
| Max control period with `calib` | (copy) | ____ ms |
| ISR → thread latency (`lat_peak_us`) | — | ____ µs |
| Visible context-switch gap (Task C) | — | ____ µs |
| Control thread stack high-water mark | — | ____ bytes / ____ allocated |

## Tasks

### Task A — Complete the migration

Every task becomes a thread or deferred work; `main` only brings the hardware up,
starts the timer, and returns. The plan, in rate-monotonic order (shorter period,
higher priority):

| Thread | Runs | Woken by | Priority | Stack |
|---|---|---|---|---|
| `sampling_thread` | `task_sampling` | `tick_q` (from week 3) | 2 | 1536 |
| `control_thread` | `task_control` | a `k_sem` that sampling gives every 10th sample | 3 | 1024 |
| `flow_wq` (workqueue) | `task_flow_batch` | the flow ISR, once 100 pulses have piled up | 5 | 1024 |
| `display_thread` | `task_display` | `k_msleep(50)` | 7 | 2048 |
| `telemetry_thread` | `task_telemetry` | `k_sleep(K_TIMEOUT_ABS_MS(next))`, `next` += 1000 | 8 | 2048 |
| `console_thread` | `task_console` | `k_msleep(5)` between polls | 9 | 2048 |

Three rules the plan follows — know why before you type:

1. **Delete `CONFIG_MAIN_THREAD_PRIORITY=10`** from `prj.conf`. At the default
   0, `main` outranks every thread, so `init_hw()` finishes before any of them
   touches a pin.
2. **Not the system workqueue.** `k_work_submit()` uses Zephyr's shared queue,
   which runs at priority −1 — cooperative — so sampling could not preempt a
   flow batch. Start your own:

   ```c
   K_THREAD_STACK_DEFINE(flow_wq_stack, 1024);
   static struct k_work_q flow_wq;
   static struct k_work flow_work;

   /* in main, before init_hw(): */
   const struct k_work_queue_config cfg = { .name = "flow_wq" };

   k_work_queue_start(&flow_wq, flow_wq_stack,
                      K_THREAD_STACK_SIZEOF(flow_wq_stack), 5, &cfg);
   k_work_init(&flow_work, flow_work_fn);   /* flow_work_fn calls task_flow_batch() */
   ```

   and in `flow_isr`: `if (atomic_inc(&flow_pulses) + 1 >= FLOW_BATCH)
   k_work_submit_to_queue(&flow_wq, &flow_work);`
3. **Every thread blocks.** A thread that polls without sleeping owns every cycle
   below its priority — a spinning console would eat the idle thread, and next
   week's CPU-load reading with it. The S3's 128-byte RX FIFO holds ~11 ms of
   typing at 115200, so a 5 ms nap loses nothing.

- Keep the same instrumentation GPIOs (the comparison demands symmetry).
- Check: `status` answers, telemetry arrives every second, pressure still tracks
  the setpoint. The reference is [firmware/kernel/](../firmware/kernel/).
- **Evidence:** the full node running + the thread list from Task D.

### Task B — The A/B
- Repeat the week-2 measurement protocol exactly (same duration, same conditions)
  on the kernel version. Fill in the table.
- **Evidence:** complete A/B table + captures of both conditions.

### Task C — The cost
- On every 10th sample, sampling gives control's semaphore and then blocks on
  `tick_q`: the gap between `instr_samp` falling and `instr_ctrl` rising is one
  context switch plus the kernel calls around it. Measure its max.
- Estimate the overhead per second at your current load: how many switches per
  second, times that gap?
- **Evidence:** the number + the one-line calculation.

### Task D — Stack high-water marks
- Add to `prj.conf`:

  ```
  CONFIG_THREAD_NAME=y
  CONFIG_THREAD_ANALYZER=y
  CONFIG_THREAD_ANALYZER_USE_PRINTK=y
  ```

- The node has no shell — the console owns the UART — so add a `threads` command
  to `console_handle` that calls `thread_analyzer_print(0)` (header
  `zephyr/debug/thread_analyzer.h`).
- Run the node under load (flow pulses, HMI, a `calib`), then type `threads`.
- **Evidence:** the output, and which thread is closest to its limit.

## What about FreeRTOS?

The mapping is 1:1: `k_msgq`→`xQueue`, `k_sem`→`xSemaphoreGiveFromISR`/`Take`,
`k_work`→the timer-daemon task or a dedicated one, same preemptive priorities. To
measure stacks, FreeRTOS provides `uxTaskGetStackHighWaterMark()`. The practical
difference is in the defaults: FreeRTOS boots with fewer services (smaller
footprint — its strength on small chips); Zephyr ships console/log/shell ready
(its strength in larger products).

## Deliverables (RET)

- **§2 ADR-001 — Node architecture: multithreaded kernel.** Context (baseline +
  blocking command), decision, justification **citing the A/B table**, status.
- **§3 Week-4 evidence:** A/B table + measured overhead + stack high-water marks.

## Rubric (100 pts)

| | pts |
|---|---|
| **Execution** — migration complete per the mapping (20) · symmetric instrumentation (10) · thread analyzer running (10) | 40 |
| **Evidence** — A/B with a protocol identical to week 2's (20) · overhead & stack measured (10) | 30 |
| **Analysis** — ADR-001 citing numbers, with the cost acknowledged (not just the benefit) (30) | 30 |
