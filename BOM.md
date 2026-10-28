# Bill of Materials (BOM) — per group of 2–3 students

Labs are done in groups of 2–3. Each group buys one **Control Kit** (modules 0–4
and the final project). The **Hub Kit** (modules 5–6) is one per large group
(4–6, two groups merged) or lent by the lab.

> Reference prices July 2026 in COP; **check the link before buying** (they
> fluctuate by seller). On AliExpress the total drops ~40–60 % but takes 2–5
> weeks and may clear customs: order no later than weeks 1–2 of the semester
> (only for what's used from week 5 on — buy the board locally).

> **Starter board (weeks 1–2)**: the **NUCLEO-L476RG** — the board from the
> prerequisite courses, so most students already have one and the lab lends the
> rest. It's not part of the kit. Note it takes a USB **Mini-B** cable, not the
> Micro-B or C you probably have. From week 3 on, everything runs on the ESP32-S3.

## Control Kit (one per group of 2–3)

| # | Component | Qty | What for | MercadoLibre CO (approx.) | AliExpress (approx.) |
|---|-----------|-----|----------|---------------------------|----------------------|
| 1 | **ESP32-S3 DevKitC-1 N16R8** (or YD-ESP32-S3 N8R2) | 1 | The course board | [$41,000–85,000](https://listado.mercadolibre.com.co/esp32-s3-devkitc) ([option 1](https://articulo.mercadolibre.com.co/MCO-1494660367-tarjeta-desarrollo-esp32-s3-n16r8-doble-puerto-usb-tipo-c-_JM), [option 2](https://articulo.mercadolibre.com.co/MCO-1998898288-yd-esp32-s3-devkitc-n8r2-wroom-wifi-bluetooth-usb-dual-_JM)) | US$6–10 |
| 2 | **USB logic analyzer, 8 ch 24 MHz** | 1 | Measuring latency/jitter — the course's central instrument | [$30,000–50,000](https://listado.mercadolibre.com.co/analizador-logico-usb) ([with clips](https://articulo.mercadolibre.com.co/MCO-1420558229-analizador-logico-usb-24mhz-8ch-12-ganchos-de-prueba-cab-_JM)); also [Electronilab](https://electronilab.co/tienda/analizador-logico-usb-8-canales-24mhz/) | US$4–6 |
| 3 | **2.8" ILI9341 touch TFT (SPI)** | 1 | Control node's local GUI (LVGL on Zephyr) | [$35,000–60,000](https://listado.mercadolibre.com.co/ili9341) ([example](https://articulo.mercadolibre.com.co/MCO-2885980352-lcd-tft-tactil-28-pulgadas-240x320-ili9341-esp32-arduino-_JM)) | US$6–9 |
| 4 | **YF-S401 flow sensor** (or YF-S201) | 1 | "Irrigation flow": Hall pulses → interrupts, the hard sampling task | [$15,000–30,000](https://listado.mercadolibre.com.co/sensor-de-flujo-yf-s201) ([YF-S401](https://articulo.mercadolibre.com.co/MCO-865008893-sensor-de-flujo-de-agua-yf-s401-_JM)) | US$3–5 |
| 5 | **5 V mini submersible pump** + hose | 1 | The control loop's actuator | [$8,000–15,000](https://listado.mercadolibre.com.co/mini-bombas-de-agua-arduino) ([example](https://articulo.mercadolibre.com.co/MCO-524609873-mini-bomba-de-agua-sumergible-5v-proyectos-arduino-_JM)) | US$2–3 |
| 6 | **MX1508/L298N H-bridge driver** (or MOSFET module) | 1 | PWM to the pump (never straight off the GPIO) | $8,000–15,000 ([search](https://listado.mercadolibre.com.co/modulo-driver-motor-mx1508)) | US$1–2 |
| 7 | **SG90 servo** | 1 | The "valve": a second output with a deadline | $10,000–15,000 ([search](https://listado.mercadolibre.com.co/servo-sg90)) | US$2 |
| 8 | **DS18B20** (probe) or thermistor | 1 | Temperature: slow sensor for the soft telemetry | $8,000–15,000 ([search](https://listado.mercadolibre.com.co/sensor-ds18b20)) | US$1–2 |
| 9 | **Breadboard kit**: 830-point breadboard, M-M/M-F jumpers, LEDs, resistors, buttons, potentiometer ("pressure"), breadboard supply | 1 | The base of every lab | $30,000–50,000 ([search kits](https://listado.mercadolibre.com.co/kit-protoboard-arduino)) | US$6–10 |
| 10 | USB-C **data** cable | 1–2 | Programming/monitor (check it's not charge-only) | $8,000–15,000 | US$1–2 |
| 11 | **0.96" SSD1306 128×64 OLED (I²C)** *(optional)* | 1 | The superloop's HMI (weeks 2–4) — the node runs without it | [$10,000–20,000](https://listado.mercadolibre.com.co/pantalla-oled-096-i2c) | US$1–2 |
| 12 | **SN65HVD230 CAN transceiver module (3.3 V)** | 1 | The node's CAN link to the Hub (project, weeks 11–14) | [search](https://listado.mercadolibre.com.co/sn65hvd230) | US$1–5 |

**Control Kit total**: ~**$190,000–320,000 COP** per group (≈ $65,000–110,000 per
student in groups of 3). Via AliExpress: ≈ **US$32–50** + shipping.

## Hub Kit (one per large group of 4–6, modules 5–6)

| # | Component | Qty | What for | Approx. price |
|---|-----------|-----|----------|---------------|
| 13 | **Raspberry Pi 4 (4 GB)** or Pi 5 + 32 GB microSD + official supply | 1 | The Hub (modules 5–6): PREEMPT_RT, `SCHED_DEADLINE`, GUI, routing | [$350,000–550,000](https://listado.mercadolibre.com.co/raspberry-pi-4) (verify; also [Sigma](https://www.sigmaelectronica.net/fabricante/raspberry-pi/)) |
| 14 | Hub display | 1 | Local GUI | Option A: **web HMI** (laptop browser) — $0. Option B: lab HDMI monitor — $0. Option C: 7" touchscreen ($200,000–300,000), only if the group wants it |
| 15 | **Waveshare RS485 CAN HAT** (MCP2515 + 3.3 V transceiver, 120 Ω on board) | 1 | The Hub's end of the CAN bus ([SOP-12](labs/sops/sop12_can.md)); Waveshare confirms the Pi 4B | ≈ US$16–20 abroad ([Waveshare](https://www.waveshare.com/RS485-CAN-HAT.htm)); [search locally](https://listado.mercadolibre.com.co/rs485-can-hat) |

> **Recommendation**: to contain cost, design the Hub GUI as a web HMI or LVGL on
> the lab's HDMI; the 7" touchscreen is optional. If the department can lend 4–6
> Raspberry Pis, the Hub Kit drops to just the microSD.

## Alternative local shops (Colombia)

[Electronilab](https://electronilab.co) · [Sigma Electrónica](https://www.sigmaelectronica.net) ·
Vistronica · La Red Electrónica — sometimes better price/stock than MercadoLibre
for sensors and modules; national shipping to Manizales.

## When each item is needed

- **Week 1**: the NUCLEO-L476RG and its USB Mini-B cable; the lab lends boards to whoever needs one.
- **Week 2**: logic analyzer (#2) and breadboard kit (#9) — the jitter baseline is measured here.
- **Week 3**: ESP32-S3 board (#1) — buy locally, don't wait on AliExpress.
- **Weeks 5–6**: pump, driver, flow sensor, servo, DS18B20, potentiometer, TFT display (#3–8) — the pump and the flow sensor serve week 6's optional jitter-vs-control task and the project's node.
- **Week 9**: Hub Kit (#13–14).
- **Week 11**: CAN transceiver (#12) and CAN HAT (#15), plus a twisted pair (one pair of a network cable works).
