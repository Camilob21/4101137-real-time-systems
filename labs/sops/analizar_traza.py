#!/usr/bin/env python3
"""Lab 5 (Sistemas en Tiempo Real) - saca los numeros de una traza CTF de Zephyr.  v2

Lee la captura de trace_capture.py usando el decodificador de Zephyr
(scripts/tracing/trace_viewer.py) y produce:

  0. <traza>_reparada : la misma traza sin los bytes corruptos. Si el enlace UART
     perdio bytes, el visor de Zephyr se detiene en ese punto; este archivo se
     vuelve a sincronizar y el visor puede abrirlo completo.
  1. eventos.txt : todos los eventos, uno por linea, con el MISMO indice (#) y el
     MISMO tiempo relativo que muestra el visor en modo log (tecla v) sobre la
     traza reparada.
  2. En pantalla: resumen, la cadena de UNA expropiacion dentro de calib, la de UN
     10.o tick, estadisticas de tiempos y la carga de CPU por hilo.

Nota: el tracer de Zephyr descarta los eventos generados mientras corre su propio
hilo (tracing_thread), asi que a veces falta un switched_in. El script asigna ese
tiempo al hilo que aparece en el siguiente switched_out (es el que estaba en la CPU).

Uso (Ubuntu/WSL, desde la raiz del repo, con el venv de Zephyr activo):
  python3 labs/sops/analizar_traza.py trace/normal/channel0_0 --metadata trace/metadata
  python3 labs/sops/analizar_traza.py trace/calib/channel0_0 --metadata trace/metadata
"""
import argparse
import collections
import os
import statistics
import struct
import sys

GPIO_SAMP = 1 << 4   # instr_samp = GPIO4
GPIO_CTRL = 1 << 5   # instr_ctrl = GPIO5
HDR = struct.Struct("<QH")
IDLE = "idle"


def cargar_visor(zephyr_base):
    rutas = [os.path.dirname(os.path.abspath(__file__))]
    if zephyr_base:
        rutas.insert(0, os.path.join(zephyr_base, "scripts", "tracing"))
    for r in rutas:
        if os.path.exists(os.path.join(r, "trace_viewer.py")):
            sys.path.insert(0, r)
            import trace_viewer  # noqa: E402
            return trace_viewer
    sys.exit("No encuentro trace_viewer.py: revisa ZEPHYR_BASE o copialo junto a este script.")


def limpiar(data, defs):
    """Recorre el flujo CTF y descarta los bytes que no forman eventos validos.

    Un registro se acepta si su id existe en el metadata y su marca de tiempo es
    >= la anterior y < 3 s despues. Ante un fallo se busca, byte a byte, la primera
    posicion desde la que tres registros seguidos son validos (resincronizacion).
    """
    hs = HDR.size
    n = len(data)

    def valido(off, prev_ts):
        if off + hs > n:
            return None
        ts, eid = HDR.unpack_from(data, off)
        d = defs.get(eid)
        if d is None or off + hs + d.size > n:
            return None
        if prev_ts is not None and not (prev_ts <= ts < prev_ts + 3_000_000_000):
            return None
        return ts, hs + d.size

    out = bytearray()
    off, prev = 0, None
    resync, saltados, malos, donde = 0, 0, collections.Counter(), []
    while off + hs <= n:
        r = valido(off, prev)
        if r:
            ts, size = r
            out += data[off:off + size]
            prev, off = ts, off + size
            continue
        # desincronizado: anota el id que fallo y busca donde retomar
        _, eid = HDR.unpack_from(data, off)
        malos[eid] += 1
        donde.append(prev)
        resync += 1
        p = off + 1
        while p + hs <= n:
            r1 = valido(p, prev)
            if r1:
                r2 = valido(p + r1[1], r1[0])
                if r2 and valido(p + r1[1] + r2[1], r2[0]):
                    break
            p += 1
        saltados += p - off
        off = p
    return bytes(out), resync, saltados, malos, donde


def us(ns):
    return ns / 1000.0


def stats(nombre, valores):
    if not valores:
        print(f"  {nombre:<46} (sin datos)")
        return
    v = sorted(valores)
    p99 = v[min(len(v) - 1, int(0.99 * len(v)))]
    print(f"  {nombre:<46} n={len(v):<6} min={v[0]:7.2f}  mediana={statistics.median(v):7.2f}"
          f"  p99={p99:7.2f}  max={v[-1]:7.2f}  [us]")


def main():
    ap = argparse.ArgumentParser(description="Analiza una traza CTF del nodo (Lab 5)")
    ap.add_argument("traza", help="archivo channel0_0 capturado")
    ap.add_argument("--metadata", required=True, help="trace/metadata (con el parche sleep_ticks)")
    ap.add_argument("--zephyr", default=os.environ.get("ZEPHYR_BASE", ""), help="ZEPHYR_BASE")
    ap.add_argument("--max-mb", type=float, default=4.0, help="lee solo los primeros N MB (def. 4)")
    ap.add_argument("--desde-ms", type=float, default=None, help="inicio ventana carga CPU (ms desde t0)")
    ap.add_argument("--hasta-ms", type=float, default=None, help="fin ventana carga CPU (ms desde t0)")
    ap.add_argument("--eventos", default=None, help="archivo de salida con todos los eventos")
    a = ap.parse_args()

    tv = cargar_visor(a.zephyr)
    defs, usada = tv.build_event_defs(a.metadata)
    if usada is None:
        sys.exit("No pude leer el metadata: revisa la ruta de --metadata.")

    with open(a.traza, "rb") as fh:
        crudo = fh.read(int(a.max_mb * 1024 * 1024))
    data, resync, saltados, malos, donde = limpiar(crudo, defs)
    reparada = a.traza + "_reparada"
    with open(reparada, "wb") as fh:
        fh.write(data)
    eventos_txt = a.eventos or os.path.join(os.path.dirname(a.traza) or ".", "eventos.txt")

    reader = tv.TraceReader(defs, True)
    reader.feed(data)
    offs, o = [], 0                       # posicion de cada evento dentro de data
    while o + HDR.size <= len(data):
        size = HDR.size + defs[HDR.unpack_from(data, o)[1]].size
        offs.append((o, size))
        o += size
    tr = reader.tr
    ev = tr.events
    if not ev:
        sys.exit("No se decodifico ningun evento (captura vacia o metadata equivocado).")
    t0, t1 = tr.t0, tr.t1

    def nombre(e):
        tid = e.fields.get("thread_id")
        if tid is None:
            return ""
        return e.fields.get("name") or tr.threads.get(tid, {}).get("name") or f"0x{tid:x}"

    def nm(e):
        return e.name.strip()

    def es(e, n, hilo=None):
        return nm(e) == n and (hilo is None or hilo in nombre(e))

    def gpio(e, cual, mascara):
        return nm(e) == f"gpio_port_{cual}_bits_raw_enter" and (e.fields.get("pins", 0) & mascara)

    # ---------------------------------------------------------------- eventos.txt
    with open(eventos_txt, "w") as out:
        out.write(f"{'#':>7}  {'t desde t0 [us]':>16}  evento                          campos\n")
        for i, e in enumerate(ev):
            campos = []
            for k, v in e.fields.items():
                if k == "pins" and isinstance(v, int):
                    campos.append("pins=" + ",".join(f"GPIO{b}" for b in range(32) if v >> b & 1))
                elif isinstance(v, int) and (k.endswith("id") or k == "port"):
                    campos.append(f"{k}=0x{v:x}")
                else:
                    campos.append(f"{k}={v}")
            out.write(f"{i:>7}  {us(e.ts - t0):16.3f}  {nm(e):<30}  {'  '.join(campos)}\n")

    # ---------------------------------------------------------------- resumen
    n_in = sum(1 for e in ev if es(e, "thread_switched_in"))
    n_out = sum(1 for e in ev if es(e, "thread_switched_out"))
    n_out_idle = sum(1 for e in ev if es(e, "thread_switched_out", IDLE))
    span_ms = (t1 - t0) / 1e6
    print(f"\n=== RESUMEN ({a.traza}) ===")
    print(f"  bytes leidos {len(crudo)/1024/1024:.2f} MB -> eventos validos {len(ev)}, duracion {span_ms:.1f} ms")
    print(f"  resincronizaciones (bytes perdidos/corruptos en el enlace UART): {resync}"
          f"  ({saltados} bytes descartados)")
    if malos:
        print("     ids que no existen en el metadata donde se perdio la sincronia: "
              + ", ".join(f"0x{k:x} x{v}" for k, v in malos.most_common(6)))
        for p in donde[:3]:
            if p is not None:
                print(f"     p.ej. en t = {us(p - t0)/1000:.3f} ms")
    print(f"  traza reparada (abrela con el visor): {reparada}")
    print(f"  thread_switched_in  : {n_in}")
    print(f"  thread_switched_out : {n_out}  (faltan switched_in: el tracer no se traza a si mismo)")
    cuenta = collections.Counter((nm(e)[16:], nombre(e)) for e in ev if nm(e).startswith("thread_switched_"))
    for h in sorted({h for _, h in cuenta}):
        print(f"     {h:<16} in={cuenta[('in', h)]:<6} out={cuenta[('out', h)]}")
    print("  hilos con nombre    : " + ", ".join(sorted({t['name'] for t in tr.threads.values() if t['name']})))
    huecos = [(ev[i - 1].ts, ev[i].ts) for i in range(1, len(ev)) if ev[i].ts - ev[i - 1].ts > 2_000_000]
    print(f"  huecos > 2 ms sin eventos (buffer lleno -> eventos perdidos): {len(huecos)}")
    for s, e_ in huecos[:5]:
        print(f"     de t={us(s - t0)/1000:9.3f} ms a t={us(e_ - t0)/1000:9.3f} ms  ({(e_ - s)/1e6:.1f} ms)")
    bw = [i for i, e in enumerate(ev) if nm(e) == "thread_busy_wait_enter"]
    if bw:
        ini, fin = ev[bw[0]].ts, ev[bw[-1]].ts
        print(f"  calib (k_busy_wait): primero #{bw[0]} t={us(ini - t0)/1000:.3f} ms, ultimo #{bw[-1]}"
              f" t={us(fin - t0)/1000:.3f} ms -> calib visible en la traza: {(fin - ini)/1e6:.1f} ms"
              f" de ~400 ms ({len(bw)} busy-waits de 1000)")

    # ---------------------------------------------------------------- ticks
    ticks, descartados = [], []
    for i, e in enumerate(ev):
        if nm(e) != "isr_enter":
            continue
        k = {"i_isr": i, "isr": e.ts}
        j = i + 1
        while j < len(ev) and j < i + 150:
            x = ev[j]
            n = nm(x)
            if "ready" not in k:
                if es(x, "thread_sched_ready", "sampling"):
                    k["ready"] = x.ts
                elif n == "isr_enter":
                    break                      # era otra ISR (no el tick)
            elif "in_samp" not in k:
                if es(x, "thread_switched_out"):
                    k["out_prev"], k["prev"] = x.ts, nombre(x)
                elif es(x, "thread_switched_in", "sampling"):
                    k["in_samp"] = x.ts
            elif "rise4" not in k:
                if gpio(x, "set", GPIO_SAMP):
                    k["rise4"] = x.ts
            elif "fall4" not in k:
                if gpio(x, "clear", GPIO_SAMP):
                    k["fall4"] = x.ts
            elif "pend" not in k:
                if n.startswith("semaphore_give") and "give" not in k:
                    k["give"] = x.ts
                elif es(x, "thread_sched_ready", "control"):
                    k["ready_ctrl"] = x.ts
                elif es(x, "thread_sched_pend", "sampling"):
                    k["pend"] = x.ts
            elif "out_samp" not in k:
                if es(x, "thread_switched_out", "sampling"):
                    k["out_samp"] = x.ts
            elif "next" not in k:
                if es(x, "thread_switched_in"):
                    k["in_next"], k["next"] = x.ts, nombre(x)
                elif n == "thread_switched_out":
                    k["next"] = nombre(x) + " (sin switched_in)"
                    break
                elif n == "isr_enter" and j - i > 60:
                    break
            elif "control" in k["next"] and gpio(x, "set", GPIO_CTRL):
                k["rise5"] = x.ts
                break
            elif "control" not in k["next"]:
                break
            j += 1
        if "ready" in k and "in_samp" in k:
            claves = [c for c in ("isr", "ready", "out_prev", "in_samp", "rise4", "fall4", "give", "ready_ctrl",
                                  "pend", "out_samp", "in_next", "rise5") if c in k]
            if all(k[b] - k[c] < 500_000 for c, b in zip(claves, claves[1:])):
                ticks.append(k)          # si hay un salto > 500 us dentro del tick, se perdieron eventos
            else:
                descartados.append(k)

    def cadena(k, titulo, archivo):
        print(f"\n=== {titulo} ===")
        print(f"  (indice #{k['i_isr']} en el visor sobre la traza reparada: tecla v = log;"
              f" o en {eventos_txt})")
        pasos = [("1 isr_enter (tick 1 kHz)", "isr"),
                 ("2 thread_sched_ready(sampling)  <- k_msgq_put de la ISR", "ready"),
                 (f"4a thread_switched_out({k.get('prev', '?')})  -> queda READY", "out_prev"),
                 ("4b thread_switched_in(sampling)", "in_samp"),
                 ("5 GPIO4 sube (instr_samp)", "rise4"),
                 ("  GPIO4 baja", "fall4"),
                 ("  semaphore_give (k_sem_give a control)", "give"),
                 ("  thread_sched_ready(control)", "ready_ctrl"),
                 ("6 thread_sched_pend(sampling)  <- k_msgq_get bloquea", "pend"),
                 ("7a thread_switched_out(sampling)", "out_samp"),
                 (f"7b thread_switched_in({k.get('next', '?')})", "in_next"),
                 ("  GPIO5 sube (instr_ctrl)", "rise5")]
        for txt, key in pasos:
            if key in k:
                print(f"  t={us(k[key] - t0)/1000:10.4f} ms   +{us(k[key] - k['isr']):7.2f} us   {txt}")
        if "in_next" not in k and "next" in k:
            print(f"  7b la CPU vuelve a: {k['next']}")
        recortar(k, archivo)

    def recortar(k, archivo):
        """Escribe una mini-traza de ~150 us alrededor del tick, para la captura anotada."""
        w0 = k["isr"] - 40_000
        w1 = max(v for c, v in k.items() if c in ("rise5", "in_next", "out_samp", "pend")) + 40_000
        idx = [i for i, e in enumerate(ev) if w0 <= e.ts <= w1]
        if not idx:
            return
        out = bytearray()
        for i in range(idx[0] - 1, -1, -1):  # hilo que estaba corriendo al inicio de la ventana
            if nm(ev[i]) == "thread_switched_out":
                break
            if nm(ev[i]) == "thread_switched_in":
                o, size = offs[i]
                rec = bytearray(data[o:o + size])
                struct.pack_into("<Q", rec, 0, w0)
                out += rec
                break
        for i in idx:
            o, size = offs[i]
            out += data[o:o + size]
        with open(archivo, "wb") as fh:
            fh.write(out)
        print(f"  mini-traza para la captura anotada: {archivo}")
        print(f"     t0 de la mini-traza = {us(w0 - t0)/1000:.4f} ms de la traza completa; el tick (1) esta en"
              f" +{us(k['isr'] - w0):.0f} us")

    if bw:
        c0, c1 = ev[bw[0]].ts, ev[bw[-1]].ts + 1_000_000
        calib = [k for k in ticks if "console" in k.get("prev", "") and c0 <= k["isr"] <= c1]
    else:
        calib = []
    decimo = [k for k in ticks if "control" in k.get("next", "") and "rise5" in k]
    base = os.path.dirname(a.traza) or "."
    if calib:
        cadena(calib[min(3, len(calib) - 1)], "UNA EXPROPIACION DENTRO DE calib (Task B)",
               os.path.join(base, "tick_calib"))
    else:
        print("\n(No hay ticks que expropien a la consola: esta captura no tiene calib.)")
    if decimo:
        dc = [k for k in decimo if "console" in k.get("prev", "")] or decimo   # preferible dentro de calib
        cadena(dc[min(1, len(dc) - 1)], "UN 10.o TICK: k_sem_give -> control (Task B)",
               os.path.join(base, "tick_decimo"))

    print("\n=== ESTADISTICAS (todos los ticks completos de la captura) ===")
    print(f"  ticks reconstruidos: {len(ticks)}  (dentro de calib: {len(calib)}, 10.os ticks: {len(decimo)});"
          f" descartados por eventos perdidos: {len(descartados)}")
    stats("ISR tick -> switched_in(sampling)", [us(k["in_samp"] - k["isr"]) for k in ticks])
    stats("ISR tick -> GPIO4 sube (inicio de muestreo)", [us(k["rise4"] - k["isr"]) for k in ticks if "rise4" in k])
    stats("cambio de contexto: out(X) -> in(sampling)", [us(k["in_samp"] - k["out_prev"]) for k in ticks if "out_prev" in k])
    stats("cambio de contexto: out(sampling) -> in(sig.)", [us(k["in_next"] - k["out_samp"]) for k in ticks if "in_next" in k])
    stats("10.o tick: pend(sampling) -> in(control)", [us(k["in_next"] - k["pend"]) for k in decimo])
    stats("10.o tick: GPIO4 baja -> GPIO5 sube (=Lab 4)", [us(k["rise5"] - k["fall4"]) for k in decimo if "fall4" in k])
    stats("ancho de pulso instr_samp (GPIO4)", [us(k["fall4"] - k["rise4"]) for k in ticks if "fall4" in k])

    # ---------------------------------------------------------------- carga CPU
    # Linea de tiempo: entre dos eventos de cambio corre el hilo del ultimo switched_in.
    # Si falta ese switched_in, el dueno del intervalo es el hilo que nombra el
    # siguiente switched_out (es el que sale de la CPU, luego estaba en ella).
    v0 = t0 + int(a.desde_ms * 1e6) if a.desde_ms is not None else t0 + (t1 - t0) // 20
    v1 = t0 + int(a.hasta_ms * 1e6) if a.hasta_ms is not None else t1 - (t1 - t0) // 20
    v0, v1 = max(v0, t0), min(v1, t1)
    if v1 <= v0:
        sys.exit("La ventana --desde-ms/--hasta-ms queda fuera de la traza.")
    SIN = "sin identificar"
    carga = collections.Counter()

    def suma(h, s_, f_):
        s_, f_ = max(s_, v0), min(f_, v1)
        if f_ > s_:
            carga[h] += f_ - s_

    actual, desde = None, t0
    for e in ev:
        n = nm(e)
        if n == "thread_switched_in":
            suma(actual or SIN, desde, e.ts)
            actual, desde = nombre(e), e.ts
        elif n == "thread_switched_out":
            suma(actual or nombre(e), desde, e.ts)
            actual, desde = None, e.ts
    suma(actual or SIN, desde, v1)
    span = v1 - v0
    print(f"\n=== CARGA DE CPU POR HILO, ventana {us(v0 - t0)/1000:.1f} -> {us(v1 - t0)/1000:.1f} ms"
          f" ({span/1e6:.1f} ms) ===")
    for h, ns in carga.most_common():
        print(f"  {h:<20} {ns / span * 100:7.2f} %")
    print(f"  {'SUMA':<20} {sum(carga.values()) / span * 100:7.2f} %   (las ISR cuentan dentro del hilo"
          f" interrumpido; 'sin identificar' = el tracer cuando faltan su in y su out)")
    print(f"\nListo. Todos los eventos quedaron en: {os.path.abspath(eventos_txt)}\n")


if __name__ == "__main__":
    main()
