#!/usr/bin/env python3
"""Lab 5 - repara una traza CTF con bytes perdidos o corruptos en el enlace UART/USB.

En CTF el flujo no lleva largos: si se pierde UN byte, todo lo que sigue se
decodifica como basura y el visor se detiene. Este script recorre el archivo,
copia solo registros validos (id conocido en el metadata y marca de tiempo
creciente y razonable) y, cuando encuentra basura, busca hacia adelante el
primer punto donde 8 registros seguidos vuelven a ser validos (resincroniza).

Resultado: un archivo limpio que el visor y analizar_traza.py leen completo.
Cada resincronizacion pierde solo los pocos eventos del tramo dañado (se ve
como un hueco, igual que un evento descartado por buffer lleno).

Uso (Ubuntu/WSL, raiz del repo, venv activo):
  python3 labs/sops/reparar_traza.py trace/normal/channel0_0 --metadata trace/metadata
  -> escribe trace/normal/limpio/channel0_0
"""
import argparse
import os
import struct
import sys

HDR = struct.Struct("<QH")
SALTO_MAX_NS = 2_000_000_000   # entre dos eventos seguidos no puede haber mas de 2 s
CADENA = 8                     # registros validos seguidos para aceptar una resincronizacion


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


def main():
    ap = argparse.ArgumentParser(description="Repara una traza CTF con bytes perdidos (Lab 5)")
    ap.add_argument("traza", help="archivo channel0_0 capturado")
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--zephyr", default=os.environ.get("ZEPHYR_BASE", ""))
    ap.add_argument("-o", "--salida", help="archivo limpio (def.: <carpeta>/limpio/channel0_0)")
    a = ap.parse_args()

    tv = cargar_visor(a.zephyr)
    defs, usada = tv.build_event_defs(a.metadata)
    if usada is None:
        sys.exit("No pude leer el metadata: revisa la ruta de --metadata.")
    tam = {eid: d.size for eid, d in defs.items()}

    data = open(a.traza, "rb").read()
    n = len(data)

    def registro(off, ultimo):
        """Largo del registro en off si es valido, o 0."""
        if off + HDR.size > n:
            return 0
        ts, eid = HDR.unpack_from(data, off)
        largo = tam.get(eid)
        if largo is None or off + HDR.size + largo > n:
            return 0
        if ultimo is not None and not (0 <= ts - ultimo <= SALTO_MAX_NS):
            return 0
        if ultimo is None and ts > 10**15:     # mas de ~11 dias desde el arranque: basura
            return 0
        return HDR.size + largo

    def cadena_ok(off, ultimo):
        for _ in range(CADENA):
            r = registro(off, ultimo)
            if not r:
                return False
            ultimo = HDR.unpack_from(data, off)[0]
            off += r
            if off >= n:
                return True
        return True

    out = bytearray()
    off, ultimo, eventos = 0, None, 0
    resync = []
    while off + HDR.size <= n:
        r = registro(off, ultimo)
        if r and (ultimo is not None or cadena_ok(off, ultimo)):
            out += data[off:off + r]
            ultimo = HDR.unpack_from(data, off)[0]
            off += r
            eventos += 1
            continue
        ini = off
        off += 1
        while off + HDR.size <= n and not cadena_ok(off, ultimo):
            off += 1
        resync.append((ini, off - ini, ultimo))
        if off + HDR.size > n:
            break

    salida = a.salida or os.path.join(os.path.dirname(a.traza) or ".", "limpio", os.path.basename(a.traza))
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    with open(salida, "wb") as f:
        f.write(out)

    t0 = HDR.unpack_from(out, 0)[0] if out else 0
    print(f"archivo original : {n} bytes")
    print(f"archivo limpio   : {len(out)} bytes, {eventos} eventos -> {salida}")
    print(f"bytes descartados: {n - len(out)} ({(n - len(out)) / max(1, n) * 100:.3f} %)")
    print(f"resincronizaciones (tramos danados): {len(resync)}")
    for ini, largo, ult in resync[:15]:
        t = (ult - t0) / 1e6 if ult is not None else 0.0
        print(f"   en byte {ini:>9}: {largo:>5} bytes de basura, despues de t={t:9.3f} ms")
    if len(resync) > 15:
        print(f"   ... y {len(resync) - 15} mas")
    if out:
        print(f"duracion de la traza limpia: {(ultimo - t0) / 1e6:.1f} ms")


if __name__ == "__main__":
    main()
