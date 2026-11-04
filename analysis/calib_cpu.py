#!/usr/bin/env python3
"""Lab 6, Task C — the console's CPU per `calib` settle, from a week-5 CTF trace.

    python3 analysis/calib_cpu.py trace/channel0_0 --metadata trace/metadata

Uses Zephyr's own trace viewer ($ZEPHYR_BASE/scripts/tracing/trace_viewer.py) to
decode the trace, then lists the console thread's running spans. After ADR-005
each settle is one short span (wake, read the sensor, go back to sleep): the
median span x 1000 is calib's CPU. The trace drops many spans (the 1000 sleeps
flood the link), which is why the per-settle median is used, not the sum.
"""
import argparse
import os
import statistics
import sys

ap = argparse.ArgumentParser()
ap.add_argument("trace")
ap.add_argument("--metadata", default=None)
ap.add_argument("--thread", default="console", help="substring of the thread name")
ap.add_argument("--rounds", type=int, default=1000)
ap.add_argument("--gap", type=float, default=2.0,
                help="ms: console spans closer than this count as calib (default 2)")
args = ap.parse_args()

zb = os.environ.get("ZEPHYR_BASE")
if not zb:
    sys.exit("ZEPHYR_BASE is not set: source zephyr-env.sh first")
sys.path.insert(0, os.path.join(zb, "scripts", "tracing"))
try:
    import trace_viewer as tv
except ImportError as e:
    sys.exit(f"cannot import trace_viewer.py from $ZEPHYR_BASE/scripts/tracing: {e}")

meta = tv.find_metadata(args.trace, args.metadata)
defs, _ = tv.build_event_defs(meta)


HDR = tv.HDR  # <timestamp u64, id u16>
MAX_DT = 500_000_000  # ns: a real next event is never this far ahead


def rec_at(buf, off):
    """(ts, length) of a record starting at off, or None if the id is unknown."""
    if off + HDR.size > len(buf):
        return None
    ts, eid = HDR.unpack_from(buf, off)
    d = defs.get(eid)
    if d is None or off + HDR.size + d.size > len(buf):
        return None
    return ts, HDR.size + d.size


def chain_ok(buf, off, prev_ts, n=6):
    """True if n records starting at off have known ids and timestamps that move
    forward by less than MAX_DT: a real event boundary, not noise."""
    t = prev_ts
    for _ in range(n):
        r = rec_at(buf, off)
        if r is None:
            return off >= len(buf)  # clean end of file
        ts, ln = r
        if t is not None and (ts < t or ts - t > MAX_DT):
            return False
        t = ts
        off += ln
    return True


def parse_resync(path):
    """Like trace_viewer.parse_trace, but when bytes were lost on the serial link
    it skips to the next real event boundary and goes on. Every record is checked
    against the ones after it before it is kept, so a corrupted record that happens
    to carry a valid id is not taken. Returns the trace and the losses."""
    with open(path, "rb") as fh:
        raw = fh.read()
    keep = []
    off, prev, skipped, gaps = 0, None, 0, 0
    n = len(raw)
    while off + HDR.size <= n:
        if chain_ok(raw, off, prev):
            ts, ln = rec_at(raw, off)
            keep.append(raw[off:off + ln])
            prev = ts
            off += ln
            continue
        k = off + 1  # lost bytes: search the next boundary
        while k + HDR.size <= n and not chain_ok(raw, k, prev):
            k += 1
        skipped += k - off
        gaps += 1
        off = k
    r = tv.TraceReader(defs, True)
    r.feed(b"".join(keep))
    return r.tr, skipped, gaps, n


tr, skipped, gaps, total = parse_resync(args.trace)
if not tr.events:
    sys.exit("no events decoded")
if gaps:
    print(f"link losses: {gaps} gap(s), {skipped} of {total} bytes skipped "
          f"({100 * skipped / total:.2f} %); decoding resumed after each")

tids = [tid for tid, t in tr.threads.items() if args.thread in (t.get("name") or "")]
if not tids:
    names = ", ".join(sorted((t.get("name") or "?") for t in tr.threads.values()))
    sys.exit(f"no thread named *{args.thread}*; threads in the trace: {names}")

all_spans = sorted((s, e) for s, e, tid in tr.segments if tid in tids and e >= s)
print(f"trace span: {(tr.t1 - tr.t0) / 1e6:.1f} ms, {len(tr.events)} events, "
      f"console spans: {len(all_spans)}")
if not all_spans:
    sys.exit("the console never ran inside this trace")
def select_calib(all_spans, win_ns=50_000_000, merge_ns=50_000):
    """Find calib inside the console's spans.
    1. Merge pieces split by a preemption (gap < 50 us): one wake = one settle.
    2. Outside calib the console wakes every 5 ms (~10 wakes per 50 ms); inside it
       every ~0.5 ms, minus what the link dropped. The longest run of 50 ms windows
       with at least half the densest window's wakes is calib."""
    merged = []
    for s_, e_ in all_spans:
        if merged and s_ - merged[-1][1] < merge_ns:
            merged[-1][1] = max(merged[-1][1], e_)
        else:
            merged.append([s_, e_])
    starts = [m[0] for m in merged]
    j, counts = 0, []
    for i, t in enumerate(starts):
        while j < len(starts) and starts[j] < t + win_ns:
            j += 1
        counts.append(j - i)
    if not counts:
        return [], 0
    thr = max(15, max(counts) // 2)
    best, cur = (0, -1), None
    for i, c in enumerate(counts):
        if c >= thr:
            cur = i if cur is None else cur
            if i - cur > best[1] - best[0]:
                best = (cur, i)
        else:
            cur = None
    if best[1] < 0:
        return [], thr
    t0, t1 = starts[best[0]], starts[best[1]] + win_ns
    return [(a, b) for a, b in merged if t0 <= a < t1], thr


spans, thr = select_calib(all_spans)
if not spans:

    gaps = sorted((all_spans[i + 1][0] - all_spans[i][1]) / 1e6 for i in range(len(all_spans) - 1))
    lens = sorted((e - s) / 1e3 for s, e in all_spans)
    print("\nDIAGNOSTIC: no dense burst of console wakes (calib) found")
    print("  first console span at", f"{(all_spans[0][0] - tr.t0) / 1e6:.1f} ms,",
          "last at", f"{(all_spans[-1][0] - tr.t0) / 1e6:.1f} ms")
    print("  5 smallest gaps between console spans (ms):", [round(g, 3) for g in gaps[:5]])
    print("  5 longest console spans (us):", [round(x, 1) for x in lens[-5:]])
    print("  gaps < 1 ms:", sum(g < 1 for g in gaps), "| < 5 ms:", sum(g < 5 for g in gaps),
          "| < 10 ms:", sum(g < 10 for g in gaps))
    sys.exit("no calib burst found: start the capture first, THEN type calib, "
             "wait 2 s, THEN Ctrl-C")
lens_us = [(e - s) / 1000 for s, e in spans]
med = statistics.median(lens_us)
lens_sorted = sorted(lens_us)
p90 = lens_sorted[int(0.9 * (len(lens_sorted) - 1))]

print(f"thread(s): {', '.join(tr.threads[t]['name'] for t in tids)}")
win_ms = (spans[-1][1] - spans[0][0]) / 1e6
print(f"console running spans: {len(all_spans)} in total; calib found from "
      f"t = {(spans[0][0] - tr.t0) / 1e6:.1f} ms to {(spans[-1][1] - tr.t0) / 1e6:.1f} ms "
      f"({win_ms:.1f} ms), {len(spans)} settles kept of {args.rounds}")
if not 250 <= win_ms <= 900:
    print("  WARNING: calib should last ~500 ms here; check this window in trace_viewer")
print(f"  CPU per settle: mean {statistics.mean(lens_us):.2f} us, median {med:.2f} us, p90 {p90:.2f} us, max {max(lens_us):.2f} us")
print(f"  console CPU in the kept settles: {sum(lens_us) / 1000:.3f} ms")
print(f"calib CPU estimate = median span x {args.rounds} = {med * args.rounds / 1000:.3f} ms")
