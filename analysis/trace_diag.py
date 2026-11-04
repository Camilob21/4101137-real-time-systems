#!/usr/bin/env python3
"""Why does a CTF trace stop decoding early? Finds the event the metadata does not
describe and, with --fix, appends its description to the metadata.

    python3 analysis/trace_diag.py trace/channel0_0 --metadata trace/metadata
    python3 analysis/trace_diag.py trace/channel0_0 --metadata trace/metadata --fix

A CTF reader needs every event's length. When the firmware emits an event the
metadata lacks, the viewer stops there and everything after it is lost. The fields
are taken from the firmware's own $ZEPHYR_BASE/subsys/tracing/ctf/ctf_top.h, so the
added description matches what the node emits.
"""
import argparse
import os
import re
import sys

ap = argparse.ArgumentParser()
ap.add_argument("trace")
ap.add_argument("--metadata", required=True)
ap.add_argument("--fix", action="store_true", help="append the missing event(s) to the metadata")
args = ap.parse_args()

zb = os.environ.get("ZEPHYR_BASE")
if not zb:
    sys.exit("ZEPHYR_BASE is not set: source zephyr-env.sh first")
sys.path.insert(0, os.path.join(zb, "scripts", "tracing"))
import trace_viewer as tv  # noqa: E402

top_h = os.path.join(zb, "subsys", "tracing", "ctf", "ctf_top.h")
top = open(top_h).read()
enum = {int(v, 16): n for n, v in re.findall(r"CTF_EVENT_(\w+)\s*=\s*(0x[0-9A-Fa-f]+)", top)}
CTYPES = {"uint8_t", "int8_t", "uint16_t", "int16_t", "uint32_t", "int32_t", "uint64_t", "int64_t"}

with open(args.trace, "rb") as fh:
    raw = fh.read()


def decode():
    defs, _ = tv.build_event_defs(args.metadata)
    r = tv.TraceReader(defs, True)
    r.feed(raw)
    return r


def stanza_for(eid):
    name = enum.get(eid)
    if not name:
        return None, f"id 0x{eid:X} is not in {top_h}: the trace and this Zephyr do not match"
    m = re.search(r"static inline void ctf_top_\w+\(([^)]*)\)\s*\{[^}]*?CTF_EVENT_"
                  + name + r"\)\s*(?:,([^;]*))?\);", top, re.S)
    if not m:
        return None, f"CTF_EVENT_{name} (0x{eid:X}): its emitter was not found in ctf_top.h"
    params = [p.strip() for p in m.group(1).split(",") if p.strip() and p.strip() != "void"]
    fields = []
    for p in params:
        t, _, n = p.rpartition(" ")
        if t not in CTYPES:
            return None, f"CTF_EVENT_{name}: field type '{t}' needs a hand-written description"
        fields.append(f"\t\t{t} {n};")
    body = "\n".join(fields) if fields else ""
    st = (f"\nevent {{\n\tname = {name.lower()};\n\tid = 0x{eid:X};\n"
          f"\tfields := struct {{\n{body}\n\t}};\n}};\n")
    return st, None


for attempt in range(20):
    r = decode()
    tr = r.tr
    span = (tr.t1 - tr.t0) / 1e6 if tr.events else 0
    left = len(r._buf)
    print(f"decoded {len(tr.events)} events, {span:.1f} ms; "
          f"{left} of {len(raw)} bytes not decoded")
    if not r._desync:
        print("OK: the whole trace decodes")
        break
    hsz = r.hdr.size
    ts, eid = r.hdr.unpack_from(r._buf, 0)
    print(f"stops at an event the metadata does not describe: id 0x{eid:X} "
          f"({'CTF_EVENT_' + enum[eid] if eid in enum else 'unknown to this Zephyr'})")
    st, err = stanza_for(eid)
    if err:
        sys.exit(err)
    if not args.fix:
        print("description it needs:" + st)
        print("re-run with --fix to append it to", args.metadata)
        break
    with open(args.metadata, "a") as fh:
        fh.write(st)
    print(f"appended {enum[eid].lower()} to {args.metadata}; decoding again\n")
