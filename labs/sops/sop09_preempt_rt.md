# SOP-09 — PREEMPT_RT on the SBC + cyclictest

- **Serves:** [lab09_preempt_rt.md](../lab09_preempt_rt.md) and [lab10_deadline_isolation.md](../lab10_deadline_isolation.md)
- **Hardware:** Raspberry Pi 4/5, 32 GB microSD, wired Ethernet recommended.

Steps, checks, and troubleshooting only — the *why* lives in the lab.

> **Draft** — commands pending validation on course hardware.

## 1. The RT kernel

**Route A — course image** (preferred): flash the course-prepared image
(instructor's drive) with Raspberry Pi Imager; user `greenfield`, SSH enabled.
Skip to step 2.

**Route B — Ubuntu Pro** (self-service): flash **Ubuntu Server 24.04 LTS
(64-bit)** with Raspberry Pi Imager, then on the Pi:

```bash
sudo pro attach <token>          # free personal token from ubuntu.com/pro
sudo pro enable realtime-kernel --variant raspi
sudo reboot
```

**Verify (either route):**

```bash
uname -v
```

The output must contain `PREEMPT_RT`. No `PREEMPT_RT`, no lab.

## 2. Tools

```bash
sudo apt update
sudo apt install rt-tests stress-ng iperf3 python3-matplotlib
```

**Verify:** `cyclictest --help` prints usage.

## 3. The measurement run

One command per table row, output to a file (the plot script reads these):

```bash
sudo cyclictest -m -Sp90 -i 1000 -h 400 -D 5m -q > stock_idle.txt
```

Load, when the row asks for it (run in parallel, then repeat cyclictest):

```bash
stress-ng --cpu 0 --io 2 &            # on the Pi
ping -f <pi-ip>                        # from a laptop (real traffic)
```

Name the four files `stock_idle.txt`, `stock_load.txt`, `rt_idle.txt`,
`rt_load.txt`. Kill the load between runs (`kill %1`; stop the ping).

**Verify:** the file ends with `# Histogram` lines and per-thread `# Max Latencies`.

## 4. Plot

```bash
python3 plot_cyclictest.py stock_idle.txt stock_load.txt rt_idle.txt rt_load.txt
```

[`plot_cyclictest.py`](plot_cyclictest.py) (this directory) overlays the
histograms, log-scale, one line per file, max annotated. Output: `cyclictest.png`.

## 5. Isolation (week 10)

Edit the kernel command line — one single line, append:

```
isolcpus=3 nohz_full=3 rcu_nocbs=3
```

- Ubuntu on Pi: `/boot/firmware/cmdline.txt` · course image: same path. Reboot.

**Verify:**

```bash
cat /sys/devices/system/cpu/isolated      # → 3
```

Pin, contract and steer (lab 10's rows):

```bash
sudo taskset -c 3 chrt -f 90 ./pump_loop &        # rows 1–2: FIFO on core 3
ps -o pid,psr,comm -p $!                          # PSR must say 3
sudo taskset -c 3 chrt -f 95 ./hog &              # rows 2–3: the hog, same core
DL="--sched-runtime 2000000 --sched-deadline 10000000 --sched-period 10000000"
sudo taskset -c 3 chrt -d $DL 0 ./pump_loop &     # rows 3, 5, 6: DEADLINE on core 3
sudo chrt -d $DL 0 ./pump_loop &                  # row 4: DEADLINE on cores 0–2
grep . /proc/irq/*/smp_affinity_list              # where IRQs land
echo 0-2 | sudo tee /proc/irq/<N>/smp_affinity_list   # move one off core 3
```

A `SCHED_DEADLINE` task's affinity must cover its whole scheduling domain: all of
cores 0–2, or the isolated core 3 alone. Set the affinity first and the policy
second, as above; `taskset` on a task that is already DEADLINE is refused.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `uname -v` has no `PREEMPT_RT` | Booted the stock kernel | Route B: `pro status` shows the service enabled? re-enable + reboot; course image: re-flash |
| `cyclictest: Operation not permitted` | Not root / no RT privileges | Run with `sudo` |
| Max latency in the *ms* range even on RT | CPU frequency scaling or SD-card stalls | `sudo cpupower frequency-set -g performance`; don't run `apt` during a capture |
| `pro enable realtime-kernel` refuses | Token not attached / not personal plan | `pro attach` first; personal tokens allow 5 machines |
| Histogram empty in the output file | Forgot `-h 400` or `-q` swallowed by a typo | Re-run with the exact step-3 line |
| `isolated` shows empty after reboot | cmdline edited in the wrong file or line broken in two | The Pi cmdline is **one line**; confirm the file is `/boot/firmware/cmdline.txt` |
| `chrt -d` fails with `Operation not permitted` | Affinity narrower than the domain (e.g. `taskset -c 2`), or the policy set before the affinity | Core 3 alone or cores 0–2 whole; `taskset -c 3 chrt -d …` in that order |
| Loop lands on core 3 but still jitters | IRQs still pointed at core 3 | Move them (step 5) — that's row 6 of lab 10, not a bug |
