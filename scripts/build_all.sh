#!/usr/bin/env bash
# Build every course firmware on every board it supports: the list CI runs.
# Run from anywhere inside the course's west workspace. Logs: build/ci/*.log
set -euo pipefail
cd "$(dirname "$0")/.."
out=${BUILD_ROOT:-build/ci}
mkdir -p "$out"
fail=0

build() {  # app board [cmake args...]; SB=1 builds with sysbuild
	local app=$1 board=$2
	shift 2
	local name
	name="$(basename "$app")-${board//\//_}${*:+-$(echo "$*" | md5sum | cut -c1-6)}"
	if west build -p ${SB:+--sysbuild} -b "$board" "$app" -d "$out/$name" -- "$@" >"$out/$name.log" 2>&1; then
		echo "ok    $app  $board  $*"
	else
		echo "FAIL  $app  $board  $*  (log: $out/$name.log)"
		fail=1
	fi
}

S3=esp32s3_devkitc/esp32s3/procpu

build firmware/superloop nucleo_l476rg
build firmware/superloop nucleo_l476rg -DEXTRA_CONF_FILE=nocache.conf
build firmware/superloop nucleo_l476rg -DEXTRA_CONF_FILE=display.conf -DEXTRA_DTC_OVERLAY_FILE=pot_nucleo.overlay
build firmware/superloop stm32c0116_dk
build firmware/superloop $S3
build firmware/superloop esp32c6_devkitc/esp32c6/hpcore
build firmware/superloop native_sim/native/64
build firmware/sampling_thread $S3
build firmware/sampling_thread $S3 -DEXTRA_CONF_FILE=display.conf -DEXTRA_DTC_OVERLAY_FILE=pot_esp32s3.overlay
build firmware/kernel $S3
build firmware/kernel $S3 -DEXTRA_CONF_FILE=trace.conf -DEXTRA_DTC_OVERLAY_FILE=uart_trace.overlay
build firmware/kernel $S3 -DEXTRA_DTC_OVERLAY_FILE=can_esp32s3.overlay
build firmware/kernel native_sim/native/64 -DCONFIG_THREAD_ANALYZER=n
SB=1 build firmware/amp_node/app_procpu $S3
SB=1 build firmware/amp_node/app_procpu $S3 -Dapp_appcpu_EXTRA_CONF_FILE=iram.conf

exit $fail
