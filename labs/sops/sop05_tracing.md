# SOP-05 — Zephyr tracing on the node (SystemView / CTF)

- **Serves:** [lab05_tracing.md](../lab05_tracing.md)
- **Hardware:** ESP32-S3 DevKitC; Route A needs a SEGGER J-Link probe, Route B needs only the USB cable + a spare UART.

Steps, checks, and troubleshooting only — the *why* lives in the lab.

> **Draft** — commands pending validation on course hardware.

Both routes need named threads:

```ini
CONFIG_THREAD_NAME=y
```

## Route A — SystemView over RTT (J-Link probe)

### A1. Enable it

```ini
CONFIG_TRACING=y
CONFIG_SEGGER_SYSTEMVIEW=y
CONFIG_USE_SEGGER_RTT=y
CONFIG_SEGGER_SYSVIEW_RTT_BUFFER_SIZE=8192
```

Rebuild and flash the node as usual.

### A2. Capture

1. Wire the J-Link to the S3's JTAG pins (MTMS/MTDI/MTCK/MTDO + GND); power stays USB.
2. Open **SEGGER SystemView** → Target → Start Recording; device `ESP32-S3`,
   interface JTAG.

**Verify:** the thread lanes appear with your thread names (`control`, `sampling`,
`console`…), events streaming.

## Route B — CTF over UART (no probe)

### B1. Enable it

```ini
CONFIG_TRACING=y
CONFIG_TRACING_CTF=y
CONFIG_TRACING_BACKEND_UART=y
```

Point tracing at a UART that is **not** the console (second USB-UART adapter on two
free pins), via a devicetree overlay:

```dts
/ {
    chosen {
        zephyr,tracing-uart = &uart1;
    };
};
```

### B2. Capture the raw stream

```bash
# capture ~60 s of raw CTF bytes (adjust the tty)
timeout 60 cat /dev/ttyUSB1 > channel0_0
```

### B3. Convert and view

```bash
sudo apt install babeltrace2 python3-bt2
mkdir trace && cp channel0_0 trace/
cp $ZEPHYR_BASE/subsys/tracing/ctf/tsdl/metadata trace/
babeltrace2 trace/ > trace.txt        # text timeline
```

For a graphical timeline, open the `trace/` directory in **Eclipse TraceCompass**
(File → Open Trace).

**Verify:** `trace.txt` shows `thread_switched_in` / `thread_switched_out` events
with your thread names and monotonic timestamps.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| SystemView connects but no events | RTT buffer overflow at high event rate | Increase `CONFIG_SEGGER_SYSVIEW_RTT_BUFFER_SIZE`; lower the event rate (`CONFIG_TRACING_ISR=n` if ISR events flood) |
| Threads show as addresses, not names | `CONFIG_THREAD_NAME` missing | Add it and rebuild |
| `babeltrace2` errors on the trace | Missing/mismatched `metadata`, or bytes lost on UART | Re-copy `metadata` from *your* Zephyr checkout; lower the trace UART baud; re-capture |
| Garbage mixed into the CTF file | Tracing sharing the console UART | Use a separate UART (the overlay above); never trace over the console |
| J-Link doesn't see the S3 | JTAG pins wrong or claimed by the app | Check MTMS=42, MTDI=41, MTCK=39, MTDO=40 on the DevKitC; free those pins in the overlay |
| Trace timestamps look compressed/wrong | Timer frequency mismatch in viewer | In SystemView set the CPU frequency to the S3's actual clock (240 MHz default) |
