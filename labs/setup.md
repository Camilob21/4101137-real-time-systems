# Pre-course setup — before week 1

Work **at home, before the first class**. Week 1 only *verifies* this; if you show up
without the environment, you lose the lab. Native Ubuntu or WSL2 (Windows); for WSL2,
the tested guide is [wsl2-embedded-dev-setup](https://github.com/saacifuentesmu/wsl2-embedded-dev-setup).

The course pins its Zephyr version in [west.yml](../west.yml): your laptop, your
partner's and the course CI build the same tree all semester.

## 1. Host packages

Follow Zephyr's [Getting Started](https://docs.zephyrproject.org/latest/develop/getting_started/index.html)
up to and including **Install dependencies** (the `apt install` line). Stop there: the
next steps here replace its `west init`.

## 2. Your fork and the course workspace

Fork [the course repository](https://github.com/saacifuentesmu/4101137-real-time-systems)
on GitHub (one fork per pair is enough; add your partner as collaborator). Your fork is
where your firmware changes and your RET live.

```bash
python3 -m venv ~/rts/.venv && source ~/rts/.venv/bin/activate
pip install west
west init -m https://github.com/<your-user>/4101137-real-time-systems ~/rts
cd ~/rts
west update --narrow -o=--depth=1     # ~8 min, ~2 GB: only the modules this course uses
west packages pip --install            # Zephyr's Python requirements
west sdk install -t arm-zephyr-eabi xtensa-espressif_esp32s3_zephyr-elf
west blobs fetch hal_espressif
```

Every new terminal:

```bash
source ~/rts/.venv/bin/activate && source ~/rts/zephyr/zephyr-env.sh
```

Course commands run from `~/rts/4101137-real-time-systems`; commands that start with
`zephyr/` run from `~/rts`.

## 3. Build, without any hardware

```bash
cd ~/rts
west build -p -b native_sim/native/64 zephyr/samples/hello_world
./build/zephyr/zephyr.exe            # Ctrl-C to stop
```

**Verify:** `Hello World! native_sim/native/64` is printed.

## 4. Build and flash a real board

```bash
cd ~/rts
west build -p -b nucleo_l476rg zephyr/samples/basic/blinky && west flash
```

`west flash` on the NUCLEO uses STM32CubeProgrammer (`STM32_Programmer_CLI` on your
`PATH`, installed in the prerequisite courses); with OpenOCD installed instead,
`west flash -r openocd`. For the ESP32-S3 (week 3), the same with
`-b esp32s3_devkitc/esp32s3/procpu zephyr/samples/hello_world`.

**Verify:** the NUCLEO's green LED blinks.

## 5. Serial-port access

```bash
sudo usermod -aG dialout $USER   # log out and back in
```

On WSL2, pass the USB device through with `usbipd-win` (covered in the WSL2 guide).

## 6. CI comes with the fork

Every push to your fork builds all the course firmware
([.github/workflows/ci.yml](../.github/workflows/ci.yml)). Enable Actions on the fork
once (GitHub → your fork → Actions). The same builds run locally with
`scripts/build_all.sh`.

## Week-1 checklist

- [ ] `west --version` responds in a new terminal (after the two `source` lines).
- [ ] `hello_world` runs on `native_sim/native/64`.
- [ ] Blinky runs on the NUCLEO-L476RG.
- [ ] Your user is in the `dialout` group.
- [ ] Your fork exists, with Actions enabled.

Problems? Bring the exact error (text, not a photo) to week 1 — the lab starts by
fixing whatever is missing.
