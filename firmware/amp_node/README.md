# firmware/amp_node — week 8 on: the node on two cores

The [kernel](../kernel/) node split across the S3's cores, built in week 8's guided
session ([lab08](../../labs/lab08_amp.md), [SOP-08](../../labs/sops/sop08_amp.md))
and carried into the project.

| Core | Image | Runs | Pins |
|---|---|---|---|
| APPCPU | [app_appcpu/](app_appcpu/) | sampling (1 kHz), control (10 ms), the e-stop check, the valve PWM, on the synthetic plant | `instr_samp` GPIO4, `instr_ctrl` GPIO5, valve GPIO21 |
| PROCPU | [app_procpu/](app_procpu/) | console, telemetry, the flow batch, the display, a synthetic load; from week 12, CAN | `instr_cons` GPIO6, `instr_tele` GPIO7, `instr_flow` GPIO15, `instr_disp` GPIO17, `instr_ipm` GPIO18, flow input GPIO16 |

The two talk over IPM ([common/node_ipm.h](common/node_ipm.h)): APPCPU sends a
status at 10 Hz and at once when the e-stop trips, after closing the valve itself
(ADR-005); PROCPU sends `set` and `clear`. `instr_ipm` rises when PROCPU learns of
the e-stop: from the detecting `instr_samp` pulse to that edge is the inter-core hop.

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/amp_node/app_procpu --sysbuild
west flash
```

One flash writes both images (ESP simple boot, set in `app_procpu/sysbuild.conf`).
The console is PROCPU's, on the UART jack; `load on` starts the synthetic load,
which streams a 64 KB table out of flash through the cache both cores share.

`app_appcpu/iram.conf` moves the hard path to internal RAM, off that cache:

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/amp_node/app_procpu --sysbuild \
  -- -Dapp_appcpu_EXTRA_CONF_FILE=iram.conf
```

Measured on an ESP32-S3 N16R8 (2026-10-21), max sampling jitter over 60 s:

| Case | Max jitter |
|---|---|
| One core, [kernel](../kernel/) node | 2.25 µs |
| One core, plus the load thread | 10.5 µs |
| APPCPU, PROCPU idle | 0.25 µs |
| APPCPU, `load on` | 12–21 µs |
| APPCPU with `iram.conf`, `load on` | 0.25 µs |
