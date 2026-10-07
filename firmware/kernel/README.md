# firmware/kernel — week 4 reference

The [sampling_thread](../sampling_thread/) node after week 4: every superloop task
is now a thread or deferred work with its own priority, and `main` only brings the
hardware up and returns. Students build this themselves from
[lab04](../../labs/lab04_ipc.md); it is here to unblock them and to give the
instructor known-good numbers before class.

| Superloop piece | Here | Priority | Woken by |
|---|---|---|---|
| Tick ISR + flag | `tick_isr` → `tick_q` (`k_msgq`, release time) | ISR | 1 kHz `k_timer` |
| Sampling | `sampling_thread` | 2 | `tick_q` |
| Control | `control_thread` | 3 | `control_sem` (`k_sem`), given by sampling every 10th sample |
| Flow batch | `flow_work` on its own `flow_wq` | 5 | flow ISR, once 100 pulses have piled up |
| Display | `display_thread` | 7 | 50 ms sleep |
| Telemetry | `telemetry_thread` | 8 | absolute 1 s sleep (no drift) |
| Console | `console_thread` | 9 | 5 ms sleep between polls |
| `main` | bring-up, starts the timer, returns | 0 | — |

Three choices worth knowing before measuring:

- The flow batch runs on its own workqueue at priority 5. Zephyr's system
  workqueue runs at −1 (cooperative), so sampling could not preempt a batch there.
- The console sleeps between polls. Spinning at the lowest priority would take
  every idle cycle and make week 5's CPU-load reading meaningless.
- `main` keeps the default priority 0, above every thread, so bring-up finishes
  before any of them runs.

`status` reports `backlog_peak` and `lat_peak_us` as in week 3; `threads` prints
each thread's stack high-water mark (week 4, Task D). Pins, console,
`pot_esp32s3.overlay` and `display.conf` work as in the superloop.

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/kernel && west flash
west build -p -b native_sim/native/64 firmware/kernel -- -DCONFIG_THREAD_ANALYZER=n
./build/zephyr/zephyr.exe -uart_stdinout
```

Unlike the superloop, this one runs on `native_sim`: every thread blocks, so
simulated time advances. The thread analyzer isn't available there.
