#!/usr/bin/env bash
# The week-5 tracing demo (SOP-05) in one command. Plug in both S3 jacks, and the
# analyzer with D0 on GPIO4 for the cost step, then from the course repo:
#
#   scripts/trace_demo.sh          the demo: flashes the traced node, starts the
#                                  capture, opens the live viewer in its own window
#                                  and turns this terminal into the node's console
#   scripts/trace_demo.sh check    before class: the same pipeline, no windows; it
#                                  types calib itself and decodes the result
#   scripts/trace_demo.sh cost     the tracer's cost on the analyzer, on vs. off
#
# Needs a Zephyr environment: ZEPHYR_BASE set, or ZEPHYR_ENV (default
# ~/zephyrproject/env.sh) to source. Ports are found under /dev/serial/by-id;
# override with UART=... USB=...
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$PWD
if [ -z "${ZEPHYR_BASE:-}" ]; then
	# shellcheck disable=SC1090
	source "${ZEPHYR_ENV:-$HOME/zephyrproject/env.sh}"
fi
WS=$(cd "$ZEPHYR_BASE/.." && pwd)
PY=$(command -v python3)
OUT=$REPO/build/trace_demo
TRACE=$OUT/trace
BOARD=esp32s3_devkitc/esp32s3/procpu
APP=$REPO/firmware/kernel
MODE=${1:-demo}
CAP=

say() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die() { printf '\033[31m%s\033[0m\n' "$*" >&2; exit 1; }
cleanup() { [ -n "$CAP" ] && kill "$CAP" 2>/dev/null && wait "$CAP" 2>/dev/null; return 0; }
trap cleanup EXIT

find_ports() {
	UART=${UART:-$(ls /dev/serial/by-id/* 2>/dev/null | grep -Ei 'silicon_labs|cp210|1a86|qinhe|wch|ch34|ftdi' | head -1 || true)}
	[ -n "$UART" ] || die "No UART jack found: plug the S3's UART jack with a data cable (or set UART=...)."
}

wait_usb_jack() {
	for _ in $(seq 40); do
		USB=${USB:-$(ls /dev/serial/by-id/* 2>/dev/null | grep -i 'USB_JTAG' | head -1 || true)}
		[ -n "$USB" ] && return 0
		sleep 0.25
	done
	die "No USB jack after flashing: plug the S3's USB jack with a data cable (or set USB=...)."
}

build_flash() {  # build dir, cmake args...
	local dir=$1
	shift
	(cd "$WS" && west build -p auto -b "$BOARD" "$APP" -d "$dir" -- "$@") >"$dir.log" 2>&1 ||
		{ tail -20 "$dir.log"; die "Build failed (log: $dir.log)."; }
	(cd "$WS" && west flash -d "$dir" --esp-device "$UART") >>"$dir.log" 2>&1 ||
		{ tail -20 "$dir.log"; die "Flash failed (log: $dir.log)."; }
}

flash_traced() {
	say "Building and flashing the traced node (console on the USB jack, trace on the UART jack)"
	build_flash "$OUT/traced" -DEXTRA_CONF_FILE=trace.conf -DEXTRA_DTC_OVERLAY_FILE=uart_trace.overlay
	wait_usb_jack
	sleep 2
	mkdir -p "$TRACE"
	cp "$ZEPHYR_BASE/subsys/tracing/ctf/tsdl/metadata" "$TRACE/"
	cat "$APP/ctf_sleep_events.tsdl" >>"$TRACE/metadata"
	rm -f "$TRACE/channel0_0"
	echo "UART jack (trace):   $UART"
	echo "USB jack (console):  $USB"
}

start_capture() {  # [seconds]
	"$PY" labs/sops/trace_capture.py -d "$UART" -o "$TRACE/channel0_0" ${1:+-t "$1"} >"$OUT/capture.log" 2>&1 &
	CAP=$!
}

stop_capture() {
	kill "$CAP" 2>/dev/null || true
	wait "$CAP" 2>/dev/null || true
	CAP=
	cat "$OUT/capture.log"
}

console_send() {  # line: typed into the node's console
	"$PY" - "$USB" "$1" <<'EOF'
import sys, time, serial
s = serial.Serial(sys.argv[1], 115200, timeout=0.1)
for c in sys.argv[2] + "\r":
    s.write(c.encode())
    time.sleep(0.002)
time.sleep(0.2)
s.close()
EOF
}

viewer_cmd() {
	echo "$PY $ZEPHYR_BASE/scripts/tracing/trace_viewer.py $* --metadata $TRACE/metadata $TRACE/channel0_0"
}

open_viewer() {
	local cmd
	cmd="$(viewer_cmd -f); echo; read -rp 'Viewer closed. Enter closes this window.'"
	if command -v ptyxis >/dev/null; then
		ptyxis --new-window -- bash -c "$cmd" >/dev/null 2>&1 &
	elif command -v gnome-terminal >/dev/null; then
		gnome-terminal --window -- bash -c "$cmd" >/dev/null 2>&1 &
	elif command -v x-terminal-emulator >/dev/null; then
		x-terminal-emulator -e bash -c "$cmd" >/dev/null 2>&1 &
	else
		echo "Open another terminal and run:"
		echo "  $(viewer_cmd -f)"
	fi
}

analyzer_ok() {
	command -v sigrok-cli >/dev/null && "$PY" -c "import numpy" 2>/dev/null &&
		sigrok-cli --scan 2>/dev/null | grep -q fx2lafw
}

jitter() {  # label: 2 s of D0 (instr_samp, GPIO4) at 8 MHz
	sigrok-cli -d fx2lafw -c samplerate=8M --samples 16000000 -O binary -o "$OUT/la.bin" 2>/dev/null
	"$PY" - "$OUT/la.bin" "$1" <<'EOF'
import sys
import numpy as np
x = (np.fromfile(sys.argv[1], dtype=np.uint8) & 1).astype(np.int8)
d = np.diff(x)
r, f = np.flatnonzero(d == 1) + 1, np.flatnonzero(d == -1) + 1
if len(r) < 100:
    sys.exit(f"{sys.argv[2]}: no sampling edges on D0. Is D0 on GPIO4?")
f = f[f > r[0]]
k = min(len(r), len(f))
period, width = np.diff(r) / 8, (f[:k] - r[:k]) / 8
print(f"{sys.argv[2]:>12}: sampling period {period.min():7.2f}–{period.max():7.2f} µs "
      f"(max jitter {np.abs(period - 1000).max():5.2f} µs), pulse {width.mean():5.2f} µs")
EOF
	rm -f "$OUT/la.bin"
}

decode_summary() {
	"$PY" "$ZEPHYR_BASE/scripts/tracing/trace_viewer.py" --text --width 120 \
		--metadata "$TRACE/metadata" "$TRACE/channel0_0" 2>&1 | sed -n '1,3p'
}

mode_demo() {
	flash_traced
	say "Capture running; the viewer opens in its own window"
	start_capture
	sleep 1
	open_viewer
	console_send ""
	say "This terminal is the node's console: type  calib  (Enter), watch the viewer"
	echo "Viewer keys: +/- zoom, ,/. pan, <-/-> cursor, a all, v event log, m CPU load, q quit."
	echo "Ctrl-] here ends the demo."
	echo
	"$PY" -m serial.tools.miniterm --exit-char 29 --eol CR "$USB" 115200 || true
	say "Capture stopped"
	stop_capture
	echo "Static view later:  $(viewer_cmd)"
	if analyzer_ok; then
		read -rp $'\nEnter measures the tracer\'s cost on the analyzer (reflashes the plain node, ~1 min); Ctrl-C skips. ' _
		mode_cost
	fi
}

mode_check() {
	flash_traced
	say "Capturing 4 s with a calib in the middle"
	start_capture 4
	sleep 1.5
	console_send ""
	console_send calib
	wait "$CAP" || true
	CAP=
	cat "$OUT/capture.log"
	decode_summary
	"$PY" - "$ZEPHYR_BASE" "$TRACE" <<'EOF'
import os, sys
sys.path.insert(0, os.path.join(sys.argv[1], "scripts/tracing"))
import trace_viewer as tv
defs, _ = tv.build_event_defs(os.path.join(sys.argv[2], "metadata"))
tr = tv.parse_trace(os.path.join(sys.argv[2], "channel0_0"), defs)
names = sorted(t["name"] for t in tr.threads.values() if t["name"])
busy = sum(e.name == "thread_busy_wait_exit" for e in tr.events)
print("threads:", ", ".join(names))
print(f"calib busy-wait events: {busy}")
ok = {"sampling_tid", "control_tid", "console_tid"} <= set(names) and busy > 0
print("\033[32mready for class\033[0m" if ok else "\033[31msomething is missing: see above\033[0m")
sys.exit(0 if ok else 1)
EOF
	echo "The demo will open:  $(viewer_cmd -f)"
}

mode_cost() {
	analyzer_ok || die "Needs sigrok-cli, numpy and the fx2lafw analyzer (D0 on GPIO4)."
	say "The tracer's cost, measured by the instrument that has none"
	[ -n "${USB:-}" ] || flash_traced
	start_capture 4
	sleep 1
	jitter "tracing on"
	wait "$CAP" || true
	CAP=
	build_flash "$OUT/plain"
	sleep 3
	jitter "tracing off"
	echo "The board now runs the plain week-4 node (console back on the UART jack)."
}

find_ports
mkdir -p "$OUT"
case $MODE in
demo) mode_demo ;;
check) mode_check ;;
cost) mode_cost ;;
*) die "usage: scripts/trace_demo.sh [check|cost]" ;;
esac
