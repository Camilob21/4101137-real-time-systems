# Week 8 — The two cores (AMP): guided workshop
> - **Talk:** [08_freertos_multicore_wcet](presentations/08_freertos_multicore_wcet.md)
> - **Tech guide:** [SOP-08](sops/sop08_amp.md)
> - **Reading:** [READINGS.md](../READINGS.md), week 8
> - **Module:** 4
> - **Guided, not graded on its own:** what you build today is the node you take
>   into the project; checkpoint 1 runs it.

**From:** Eng. Samuel Cifuentes — *"The S3 has two cores and we're using one. The
project's node will run its hard loop alone on the second core, so today we build
that split together, step by step, and measure whether it buys the loop a better
**worst case**. Today's talk also owes you an honest answer: when FreeRTOS is the
right call, because some customer will demand it."*

| Stakeholder | Their question | How this session answers it |
|---|---|---|
| **Samuel** | Does the second core improve the tail of the distribution? | Max jitter with and without a dedicated core |
| **Gustavo** | Is the second core worth two images to maintain? | The tail numbers next to the cost, in ADR-003 |
| **Edwin** | How long does an e-stop take to leave the node now? | The inter-core hop, measured |

## Session format (3 h)

| Time | Activity |
|---|---|
| 0:00–0:40 | Talk |
| 0:40–1:05 | **Step 1**, all together: both cores alive from one flash |
| 1:05–1:50 | **Step 2**: the node, split across the cores |
| 1:50–2:30 | **Step 3**: the tail table and the inter-core hop |
| 2:30–2:45 | **Step 4**: the hard path in internal RAM, last row |
| 2:45–3:00 | ADR-003 drafted; what changes in the project |

The instructor builds each step on the projector first; pairs follow on their own
board and don't move on until the step's check passes.

## The split

| Core | Runs | Why there |
|---|---|---|
| APPCPU | sampling at 1 kHz, control, the e-stop check, the valve output, their instrumentation GPIOs | the hard path, with nothing to share a core with |
| PROCPU | console, telemetry, display, flow batch, the synthetic load; from week 12, the CAN link | everything with a driver, a log or a person on the other end |
| IPM, APPCPU → PROCPU | the e-stop event, and a status snapshot for telemetry | the node's CAN e-stop frame leaves from PROCPU |
| IPM, PROCPU → APPCPU | `set` and `clear` from the console | |

## Steps

### Step 1 — Both cores alive
- Build and flash the `ipm_esp32` sample with sysbuild (SOP-08 §1).
- **Check:** the console shows PROCPU's requests and APPCPU's replies, from one `west flash`.

### Step 2 — The node, split
- Two apps under one sysbuild (SOP-08 §2–3), built from your week-4 node with
  [firmware/amp_node/](../firmware/amp_node/) as the reference: the APPCPU image
  carries the hard path in the table above, with no console; the PROCPU image keeps
  the rest and adds a **synthetic load** (`load on`), a thread that streams a 64 KB
  table out of flash.
- The e-stop path keeps ADR-005: sampling drives the valve low in the same job, on
  APPCPU, then tells PROCPU over IPM.
- **Check:** `instr_samp` toggles at 1 kHz while the console answers `status`;
  `set 3300` trips the e-stop, the valve drops, and PROCPU reports it.

### Step 3 — The tail table

Write the prediction column before the boards come out. Usual protocol, ≥ 60 s per
case; compare **maxima**, not averages.

| Measurement | Prediction | Your value | Note |
|---|---|---|---|
| Max loop jitter, 1 core, no load | | ____ µs | reference (wk 4) |
| Max loop jitter, 1 core, **with synthetic load** | ____ µs | ____ µs | the week-4 build plus the load thread |
| Max loop jitter on APPCPU, load on PROCPU | ____ µs | ____ µs | partitioned |
| Max loop jitter on APPCPU in IRAM, load on PROCPU | ____ µs | ____ µs | step 4 |
| Averages of all four cases | ____ | ____ | |
| Inter-core hop: the detecting `instr_samp` pulse → `instr_ipm` (GPIO18), max of 5 trips | ____ µs | ____ µs | a GPIO on each side |

### Step 4 — The hard path in internal RAM
- Row 3 may surprise you. The two cores share the flash cache, so a load streaming
  from flash on PROCPU stalls APPCPU's instruction fetches. Rebuild with
  `iram.conf` (SOP-08 §4) and fill the last jitter row.
- **Check:** `sampling_thread` sits at a `0x403…` address in the APPCPU's ELF.

### Stretch (optional) — The flow sensor as a driver
- Turn the YF-S401 reading into a minimal Zephyr driver: its own devicetree binding
  (`vendor,yf-s401`), the sensor API, and the app reaching it through
  `DEVICE_DT_GET`, with no hard-coded pin left in the app.
- **Check:** the overlay declares the sensor, and the app has no flow pin in it.

## What carries into the project

- The split above **is** the project's node: checkpoint 1 runs it, with the CAN
  link added on PROCPU ([SOP-12](sops/sop12_can.md)).
- The e-stop budget (RET §4) gains a hop: detection on APPCPU → IPM → PROCPU →
  CAN frame queued. Today's last row is its first measurement.
- ADR-003 is drafted today and closed at checkpoint 1 with the project's numbers.

## What about FreeRTOS?

Here FreeRTOS wins on this board: ESP-IDF ships real SMP on the S3 (a global
scheduler across both cores, with optional per-task pinning), while Zephyr runs the
S3's two cores only as AMP (its SMP support covers the original ESP32, not the S3).
The honest criterion: if your product is "this S3, radio on, both cores squeezed",
ESP-IDF/FreeRTOS is the mature option; if it's "a product family across varied
silicon", Zephyr.

## RET entries

- **§3 Week-8 evidence:** the table above + a one-sentence reading.
- **§2 ADR-003 — Does the hard loop live on its own core?** (draft) Decision backed
  by the tail numbers, IRAM row included; the cost: two images, no console on
  APPCPU, the inter-core hop, the IRAM it occupies.
