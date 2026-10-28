# SOP-12 — CAN between the Control node and the Hub

- **Serves:** [lab11_kickoff.md](../lab11_kickoff.md) (checkpoints 1 and 2)
- **Hardware:** ESP32-S3 DevKitC + SN65HVD230 transceiver module; Raspberry Pi 4 +
  Waveshare RS485 CAN HAT (MCP2515 + 3.3 V transceiver); a twisted pair for
  CANH/CANL plus a ground wire.
- **Firmware:** [`firmware/kernel/can_esp32s3.overlay`](../../firmware/kernel/can_esp32s3.overlay)
  (TWAI on GPIO10/11, 500 kbit/s).

Steps, checks and troubleshooting only; the *why* is in the week-12 talk.

> **Draft:** the S3 side builds on the pinned Zephyr; the bus has not yet been run
> on course hardware.

## 1. Wire the bus

| From | To |
|---|---|
| S3 GPIO10 (TWAI TX) | SN65HVD230 `CTX` (or `TX`/`D`) |
| S3 GPIO11 (TWAI RX) | SN65HVD230 `CRX` (or `RX`/`R`) |
| S3 3V3, GND | SN65HVD230 `3V3`, `GND` |
| SN65HVD230 `CANH`, `CANL` | HAT `H`, `L` (twisted pair) |
| S3 GND | Pi GND |

The bus needs 120 Ω at each end: the HAT has its own, and most SN65HVD230 modules
carry one. Measure between CANH and CANL with both boards unpowered: **≈ 60 Ω**.

**Verify:** the multimeter reads 55–65 Ω between CANH and CANL.

## 2. The Pi: CAN on the HAT

Append to `/boot/firmware/config.txt`, then reboot:

```ini
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25,spimaxfrequency=2000000
```

HATs bought before August 2019 carry an 8 MHz crystal: use `oscillator=8000000` and
`spimaxfrequency=1000000` (read the crystal's marking).

```bash
sudo apt install can-utils
sudo ip link set can0 up type can bitrate 500000
ip -details link show can0
```

**Verify:** `ip -details link show can0` reports `state ERROR-ACTIVE` and
`bitrate 500000`.

## 3. The node: bus test with the CAN sample

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu zephyr/samples/drivers/can/counter -- \
  -DEXTRA_DTC_OVERLAY_FILE=$PWD/4101137-real-time-systems/firmware/kernel/can_esp32s3.overlay \
  -DCONFIG_LOOPBACK_MODE=n
west flash
```

On the Pi:

```bash
candump -td can0
```

**Verify:** `candump` prints frames with IDs `010` and `12345`, alternating every
250 ms.

## 4. The other direction

```bash
cansend can0 010#01        # on the Pi
cansend can0 010#00
```

**Verify:** the node's console prints `LED ON`, then `LED OFF` (the S3 board has no
`led0`, so the sample prints instead of driving a pin). `can show can@6002b000` on
the node's console lists the controller state and error counters.

## 5. Into the node firmware

Build the Control node with the overlay added to the usual ones:

```bash
west build -p -b esp32s3_devkitc/esp32s3/procpu firmware/kernel -- \
  -DEXTRA_DTC_OVERLAY_FILE=can_esp32s3.overlay
```

Reach the controller with `DEVICE_DT_GET(DT_CHOSEN(zephyr_canbus))`, start it with
`can_start()`, send with `can_send()`. The frame IDs are your ADR: a lower ID wins
arbitration.

## 6. Bus load and latency

```bash
canbusload can0@500000 -r -t        # on the Pi: bus load per second
```

For the end-to-end budget, raise a node GPIO right before `can_send()` and a Pi GPIO
when the interlock thread receives the frame; the analyzer measures the gap.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot find device "can0"` | Overlay line wrong or SPI off | Re-check both `config.txt` lines; `dmesg \| grep mcp251x` shows the probe |
| `can0` in `BUS-OFF` or `ERROR-PASSIVE` | Bitrate mismatch, missing termination, or no second node acknowledging | Same bitrate on both ends; 60 Ω between CANH and CANL; the other node powered and started |
| `candump` silent, node sends | TX/RX swapped at the transceiver, or the node still in loopback | Swap GPIO10/11 wires; build with `-DCONFIG_LOOPBACK_MODE=n` |
| Frames arrive in bursts on the Pi | The MCP2515 interrupt thread runs below a busy thread | Under PREEMPT_RT the IRQ is a thread: raise its priority with `chrt` (week 10) |
| Error counters climb with long wires | Untwisted or unterminated bus | Twist CANH/CANL; keep both 120 Ω ends |
