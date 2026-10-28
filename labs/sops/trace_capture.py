#!/usr/bin/env python3
"""Capture the node's CTF trace from the UART jack (SOP-05).

    python3 trace_capture.py -d /dev/ttyACM0 -o trace/channel0_0        # Ctrl-C to stop
    python3 trace_capture.py -d /dev/ttyACM0 -o trace/channel0_0 -t 3   # 3 s

Tracing is disabled and the port drained before `enable`, so the file starts on an
event boundary even when the USB-serial bridge still holds bytes from an earlier
stream. Zephyr's trace_capture_uart.py skips that step and reads one byte per call.
"""
import argparse
import signal
import time

import serial


def stop(signum, frame):
    raise KeyboardInterrupt


def main():
    # Ctrl-C works even when started as a background job, and kill (SIGTERM) stops
    # it the same way: tracing disabled, file complete.
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-d", "--device", required=True, help="the UART jack's serial port")
    ap.add_argument("-b", "--baud", type=int, default=4_000_000, help="as in uart_trace.overlay")
    ap.add_argument("-o", "--output", default="channel0_0")
    ap.add_argument("-t", "--seconds", type=float, help="stop after this long (default: Ctrl-C)")
    a = ap.parse_args()

    port = serial.Serial(a.device, a.baud, timeout=0.05)
    port.write(b"disable\r")
    end = time.monotonic() + 0.5
    while time.monotonic() < end:
        port.read(65536)

    port.write(b"enable\r")
    total, t0 = 0, time.monotonic()
    try:
        with open(a.output, "wb", buffering=0) as out:
            while a.seconds is None or time.monotonic() - t0 < a.seconds:
                data = port.read(max(1, port.in_waiting))
                out.write(data)
                total += len(data)
    except KeyboardInterrupt:
        pass
    finally:
        port.write(b"disable\r")
        port.close()
    dt = time.monotonic() - t0
    print(f"{a.output}: {total} bytes in {dt:.1f} s ({total / dt / 1024:.0f} KiB/s)")


if __name__ == "__main__":
    main()
