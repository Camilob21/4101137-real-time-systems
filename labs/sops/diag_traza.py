import os, struct, sys
from collections import Counter
for p in (os.path.join(os.environ.get("ZEPHYR_BASE", ""), "scripts", "tracing"), "labs/sops"):
    sys.path.insert(0, p)
import trace_viewer as tv

defs, _ = tv.build_event_defs("trace/metadata")
data = open(sys.argv[1], "rb").read()
r = tv.TraceReader(defs, True)
r.feed(data)
ev = r.tr.events
print("tamano archivo :", len(data), "bytes")
print("decodificados  :", len(data) - len(r._buf), "bytes,", len(ev), "eventos,", round((r.tr.t1 - r.tr.t0) / 1e6, 1), "ms")
print("se detuvo      :", r._desync)
if len(r._buf) >= 10:
    ts, eid = struct.unpack_from("<QH", r._buf, 0)
    print("id donde paro  : 0x%x" % eid, " ts =", ts, " (ultimo ts bueno =", r.tr.t1, ")")
    print("ultimos buenos :", [e.name for e in ev[-6:]])
    print("bytes siguientes:", r._buf[:48].hex(" "))
print("switched_in por hilo:", Counter(e.fields.get("name") for e in ev if e.name == "thread_switched_in"))
print("eventos mas comunes :", Counter(e.name for e in ev).most_common(12))