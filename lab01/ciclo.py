#!/usr/bin/env python3
"""Lab 1 STR - cronometra el ciclo: Enter -> west build -> west flash -> mensaje en la consola.

Uso (Ubuntu/WSL, con el entorno activado, despues de guardar main.c):
  python3 ~/4101137-real-time-systems/lab01/ciclo.py --pristine "prueba 1"   # con -p
  python3 ~/4101137-real-time-systems/lab01/ciclo.py "prueba 2"              # incremental
El texto entre comillas es lo que el firmware imprime; al verlo en la consola se para el reloj.
"""
import argparse
import os
import subprocess
import sys
import time

import serial  # pyserial: viene con los requisitos de Zephyr

BOARD = "esp32s3_devkitc/esp32s3/procpu"
APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hello_world")

ap = argparse.ArgumentParser()
ap.add_argument("texto", help="texto que imprime el firmware (detiene el cronometro)")
ap.add_argument("--pristine", action="store_true", help="compilacion desde cero (west build -p)")
ap.add_argument("--port", default=os.environ.get("ESPTOOL_PORT", "/dev/ttyACM0"))
args = ap.parse_args()
os.environ["ESPTOOL_PORT"] = args.port  # puerto que usara west flash
if "ZEPHYR_BASE" not in os.environ:
    sys.exit("Activa primero el entorno (Paso 0): falta ZEPHYR_BASE.")
os.chdir(os.path.dirname(os.environ["ZEPHYR_BASE"]))  # raiz del workspace de west


def run(cmd):
    print("\n$ " + " ".join(cmd), flush=True)
    if subprocess.run(cmd).returncode != 0:
        sys.exit("ERROR en: " + " ".join(cmd))


t0 = time.monotonic()
run(["west", "build"] + (["-p"] if args.pristine else []) + ["-b", BOARD, APP])
t1 = time.monotonic()
run(["west", "flash"])
t2 = time.monotonic()

# Consola serie 115200 8N1. hello_world imprime UNA sola vez al arrancar, asi que
# se reinicia la placa (RTS -> pin EN, igual que esptool) para no perder el mensaje.
ser = serial.Serial()
ser.port, ser.baudrate, ser.timeout = args.port, 115200, 0.1
ser.dtr = ser.rts = False
ser.open()
try:
    ser.rts = True
    time.sleep(0.05)
    ser.rts = False
except OSError:
    pass

print(f"\n--- consola {args.port} @ 115200 8N1 ---", flush=True)
t3, buf = None, b""
while t3 is None and time.monotonic() - t2 < 15:
    buf += ser.read(ser.in_waiting or 1)
    while b"\n" in buf and t3 is None:
        line, buf = buf.split(b"\n", 1)
        txt = line.decode(errors="replace").rstrip()
        print(txt, flush=True)
        if args.texto in txt:
            t3 = time.monotonic()
ser.close()

if t3 is None:
    sys.exit(f"\nNo aparecio '{args.texto}' en 15 s: revisa que el cable este en el jack UART y repite.")

modo = "PRISTINE (con -p)" if args.pristine else "INCREMENTAL (sin -p)"
print(f"\n=== Ciclo {modo} ===")
print(f"Compilacion (west build) : {t1 - t0:6.1f} s")
print(f"Flasheo     (west flash) : {t2 - t1:6.1f} s")
print(f"Arranque -> mensaje      : {t3 - t2:6.1f} s")
print(f"TOTAL  Enter -> mensaje  : {t3 - t0:6.1f} s")
