# SOP-05 — CTF tracing on the node, over the UART jack

- **Serves:** [lab05_tracing.md](../lab05_tracing.md)
- **Hardware:** ESP32-S3 DevKitC with **both** jacks plugged in, data cables. In the
  traced build the jacks swap jobs: the trace leaves through the UART jack at
  4 Mbaud, the console moves to the USB jack (the S3's built-in USB-Serial-JTAG).
  The analyzer stays on GPIO4–7, 15, 17.
- **Firmware:** [firmware/kernel/](../../firmware/kernel/) or your week-4 node, plus
  its three tracing files: `trace.conf`, `uart_trace.overlay`, `ctf_sleep_events.tsdl`.
- **Host:** [`trace_capture.py`](trace_capture.py), in this directory.

Steps, checks and troubleshooting only; the *why* is in the
[week-5 deck](../presentations/05_tracing.md).

## 1. Find your two ports

```bash
ls -l /dev/serial/by-id/
```

The USB jack is the line with `Espressif_USB_JTAG_serial_debug_unit`. The other
line is the UART jack's bridge: `Silicon_Labs_CP2102N…` → `/dev/ttyUSB*`, or
`1a86_USB_Single_Serial…` (CH343) → `/dev/ttyACM*`. The commands below call them
`$USB` and `$UART`; set both once per terminal:

```bash
USB=/dev/serial/by-id/usb-Espressif_USB_JTAG_serial_debug_unit_<…>-if00
UART=/dev/serial/by-id/usb-<your bridge>-if00
```

**Verify:** both paths exist (`ls $USB $UART`).

## 2. Build and flash the traced node

Copy the three tracing files into your app if it isn't `firmware/kernel`, then:

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/kernel -- \
  -DEXTRA_CONF_FILE=trace.conf -DEXTRA_DTC_OVERLAY_FILE=uart_trace.overlay
west flash --esp-device $UART
```

With the pot: `-DEXTRA_DTC_OVERLAY_FILE="pot_esp32s3.overlay;uart_trace.overlay"`.

**Verify:** a terminal on the USB jack answers `status`:
`python -m serial.tools.miniterm $USB 115200` (Ctrl-] quits).

## 3. Capture

```bash
mkdir -p trace
python labs/sops/trace_capture.py -d $UART -o trace/channel0_0     # Ctrl-C to stop
```

Do what you want to trace (type `calib` in the USB-jack terminal), wait 1–2 s, then
Ctrl-C. The script prints the rate: 320–360 KiB/s, just under the 4 Mbaud link.

**Verify:** the printed size grows with the capture time (≈ 0.35 MB per second).

## 4. Metadata

```bash
cp $ZEPHYR_BASE/subsys/tracing/ctf/tsdl/metadata trace/
grep -q sleep_ticks trace/metadata || cat firmware/kernel/ctf_sleep_events.tsdl >> trace/metadata
```

The second line adds two `k_sleep` events the pinned Zephyr emits but doesn't
describe; without them decoding stops at the first `k_msleep`.

**Verify:** `grep -c sleep_ticks trace/metadata` prints a number above 0.

## 5. View

```bash
python $ZEPHYR_BASE/scripts/tracing/trace_viewer.py --metadata trace/metadata trace/channel0_0
python $ZEPHYR_BASE/scripts/tracing/trace_viewer.py --metadata trace/metadata --text trace/channel0_0 > trace.txt
```

The first opens a terminal timeline: arrow keys move, `v` toggles the raw event
log. Add `-f` to follow a capture while it runs. For a graphical timeline, open the
`trace/` directory in Eclipse TraceCompass (File → Open Trace).

**Verify:** the lanes carry your thread names (`sampling_tid`, `control_tid`, …)
and run past the first second; `trace.txt` shows `thread_switched_in` /
`thread_switched_out` events with increasing timestamps.

## 6. Tracing off, for the overhead row

Flash the plain week-4 build (no `trace.conf`, no overlay; the console returns to
the UART jack) and measure sampling jitter on the analyzer with the usual protocol.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `trace_capture.py` prints 0 bytes | Bridge can't do 4 Mbaud: CP2102N stops at 3 | Set `current-speed = <3000000>` in the overlay, rebuild, capture with `-b 3000000`; expect more drops |
| Nothing decodes | A capture joined mid-event, e.g. Zephyr's `trace_capture_uart.py` reading bytes left in the bridge | Capture with `trace_capture.py`: it drains first |
| No answer on the USB jack | Plain build flashed, or charge-only cable | The console is on the USB jack only in the traced build |
| `Permission denied` on a port | User not in `dialout` | `sudo usermod -aG dialout $USER`, log out and in |
| Lanes stop after a fraction of a second | Metadata without the sleep events | Step 4, second line |
| Gaps while `calib` runs | The tracer drains at the lowest priority; a spinning console starves it and the buffer fills | Expected: it is the cost slide, live. Read the ticks before the gap |
| Board resets when a tool opens the UART jack | That tool toggles DTR before RTS, which pulses EN | Use the tools above; they leave both lines alone |
