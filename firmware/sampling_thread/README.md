# firmware/sampling_thread — week 3 reference

The [superloop](../superloop/) after week 3: ported to the ESP32-S3 by one
overlay (`boards/esp32s3_devkitc_esp32s3_procpu.overlay`, Task A) and with
sampling moved into its first kernel thread (Task C). Students build this
themselves from [lab03](../../labs/lab03_port.md); it is here to unblock them and
to give the instructor known-good numbers before class.

| Piece | Superloop | Here |
|---|---|---|
| Tick ISR | increments `ticks_pending` | queues its release time in `tick_q` (`k_msgq`) |
| Sampling | polled by the loop | `sampling_thread`, priority 2, blocked on `tick_q` |
| Control | every 10th tick, in the loop | every 10th sample the thread raises `control_pending`; still in the loop |
| `main` | priority 0 | priority 10 (`CONFIG_MAIN_THREAD_PRIORITY`), so sampling preempts it |

`status` adds `lat_peak_us`: the worst tick-to-thread-start latency, measured by
the thread itself. Pins, console, `pot_esp32s3.overlay` and `display.conf` work as
in the superloop. Week 4 finishes the migration in [../kernel/](../kernel/).

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/sampling_thread && west flash
```
