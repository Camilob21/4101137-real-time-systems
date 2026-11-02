#!/usr/bin/env python3
"""
Lab 02 (superloop) - analiza una captura del Logic Analyzer de WaveForms (AD2)
exportada a CSV y calcula periodo, jitter, anchos de pulso (C_i) y la latencia
ISR -> loop del pulso de flujo.

Uso (en Ubuntu/WSL):
    python3 scripts/analizar_lab02.py capturas/baseline.csv
    python3 scripts/analizar_lab02.py capturas/calib.csv --rate 500000   # si el CSV no trae tiempo

Senales esperadas (nombre que se les pone en WaveForms, o el DIO por defecto):
    samp=DIO 0  ctrl=DIO 1  cons=DIO 2  tele=DIO 3  flow=DIO 4  disp=DIO 5  fin=DIO 7
"""
import argparse
import bisect
import csv
import statistics
import sys

NOMBRES = ["samp", "ctrl", "cons", "tele", "flow", "disp", "fin"]
DIO_POR_DEFECTO = {"samp": 0, "ctrl": 1, "cons": 2, "tele": 3, "flow": 4, "disp": 5, "fin": 7}
FLOW_BATCH = 100


def a_bit(txt):
    t = txt.strip().lower()
    if t in ("1", "h", "high", "true"):
        return 1
    if t in ("0", "l", "low", "false", ""):
        return 0
    try:
        return 1 if float(t) >= 0.5 else 0
    except ValueError:
        return 0


def normaliza(h):
    return h.strip().strip('"').lower().replace(" ", "").replace("_", "")


def ubicar_columnas(cabecera):
    norm = [normaliza(h) for h in cabecera]
    col_t = None
    tiempo_es_indice = False
    for i, h in enumerate(norm):
        if h.startswith("time") or h.startswith("tiempo"):
            col_t = i
            break
    if col_t is None:
        for i, h in enumerate(norm):
            if h.startswith("sample") or h.startswith("index") or h.startswith("muestra"):
                col_t = i
                tiempo_es_indice = True
                break
    cols = {}
    for nombre in NOMBRES:
        for i, h in enumerate(norm):
            if h == nombre or h.startswith(nombre + "(") or h.endswith("-" + nombre):
                cols[nombre] = i
                break
    for nombre, dio in DIO_POR_DEFECTO.items():
        if nombre in cols:
            continue
        for i, h in enumerate(norm):
            if h in (f"dio{dio}", f"din{dio}", f"dio{dio}(v)"):
                cols[nombre] = i
                break
    return col_t, tiempo_es_indice, cols


def leer(ruta, rate):
    flancos_sube = {n: [] for n in NOMBRES}
    flancos_baja = {n: [] for n in NOMBRES}
    previo = {}
    t_ini = t_fin = None
    with open(ruta, newline="", encoding="utf-8", errors="replace") as f:
        lector = csv.reader(f)
        cabecera = None
        for fila in lector:
            if not fila or fila[0].lstrip().startswith("#"):
                continue
            cabecera = fila
            break
        if cabecera is None:
            sys.exit("No encontre la fila de encabezados en el CSV.")
        col_t, es_indice, cols = ubicar_columnas(cabecera)
        if not cols:
            sys.exit(f"No reconoci ninguna senal. Encabezados del CSV: {cabecera}")
        if col_t is None or es_indice:
            if rate is None:
                sys.exit("El CSV no trae columna de tiempo en segundos: vuelve a correr con --rate <Hz>.")
        print("Columnas detectadas:", ", ".join(f"{n}->'{cabecera[i].strip()}'" for n, i in cols.items()))
        k = 0
        for fila in lector:
            if not fila or fila[0].lstrip().startswith("#"):
                continue
            try:
                if col_t is not None and not es_indice:
                    t = float(fila[col_t])
                elif col_t is not None:
                    t = float(fila[col_t]) / rate
                else:
                    t = k / rate
            except (ValueError, IndexError):
                continue
            k += 1
            if t_ini is None:
                t_ini = t
            t_fin = t
            for n, i in cols.items():
                b = a_bit(fila[i]) if i < len(fila) else 0
                p = previo.get(n)
                if p is not None and b != p:
                    (flancos_sube if b else flancos_baja)[n].append(t)
                previo[n] = b
    return cols, flancos_sube, flancos_baja, t_ini, t_fin


def anchos(sube, baja):
    out = []
    for t in sube:
        j = bisect.bisect_right(baja, t)
        if j < len(baja):
            out.append(baja[j] - t)
    return out


def periodos(sube):
    return [b - a for a, b in zip(sube, sube[1:])]


def us(x):
    return f"{x * 1e6:10.1f}"


def resumen(nombre, valores):
    if not valores:
        return f"  {nombre:<22} (sin datos)"
    return (f"  {nombre:<22} n={len(valores):6d}  prom={us(statistics.fmean(valores))} us"
            f"  min={us(min(valores))} us  max={us(max(valores))} us")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--rate", type=float, default=None, help="frecuencia de muestreo en Hz (solo si el CSV no trae tiempo)")
    ap.add_argument("--nominal-us", type=float, default=1000.0)
    a = ap.parse_args()

    cols, sube, baja, t0, t1 = leer(a.csv, a.rate)
    print(f"\nArchivo: {a.csv}")
    print(f"Duracion de la captura: {t1 - t0:.2f} s\n")

    print("== Anchos de pulso (tiempo de ejecucion C_i de cada tarea) ==")
    for n in NOMBRES:
        if n in cols and n != "fin":
            print(resumen(n, anchos(sube[n], baja[n])))

    print("\n== Periodos (flanco de subida a flanco de subida) ==")
    for n in ("samp", "ctrl", "tele", "flow", "fin"):
        if n in cols:
            print(resumen(n, periodos(sube[n])))

    if "samp" in cols and len(sube["samp"]) > 2:
        T = periodos(sube["samp"])
        nom = a.nominal_us * 1e-6
        jit = [abs(x - nom) for x in T]
        tarde = sum(1 for x in T if x > nom * 1.1)
        print("\n== MUESTREO (instr_samp) ==")
        print(f"  Periodo promedio            : {statistics.fmean(T) * 1e6:10.1f} us   (nominal {a.nominal_us:.0f} us)")
        print(f"  Periodo minimo / maximo     : {min(T) * 1e6:10.1f} us / {max(T) * 1e6:.1f} us")
        print(f"  Jitter max |T - nominal|    : {max(jit) * 1e6:10.1f} us")
        print(f"  Jitter pico a pico (max-min): {(max(T) - min(T)) * 1e6:10.1f} us")
        print(f"  Desviacion estandar         : {statistics.pstdev(T) * 1e6:10.1f} us")
        print(f"  Muestras analizadas         : {len(T) + 1}   (periodos > 1.1*nominal: {tarde})")

    if "flow" in cols and "fin" in cols and len(sube["flow"]) > 1:
        lat = []
        fin = sube["fin"]
        for prev, act in zip(sube["flow"], sube["flow"][1:]):
            i0 = bisect.bisect_right(fin, prev)
            i1 = bisect.bisect_left(fin, act)
            if i1 - i0 >= FLOW_BATCH:
                lat.append(act - fin[i0 + FLOW_BATCH - 1])
        print("\n== LATENCIA pulso de flujo (ISR) -> task_flow_batch en el loop ==")
        if lat:
            print(f"  lotes={len(lat)}  prom={statistics.fmean(lat) * 1e6:.1f} us  "
                  f"min={min(lat) * 1e6:.1f} us  max={max(lat) * 1e6:.1f} us")
        else:
            print("  No se pudo calcular (revisa que 'fin' tenga pulsos y que 'flow' tenga al menos 2 pulsos).")
    print()


if __name__ == "__main__":
    main()
