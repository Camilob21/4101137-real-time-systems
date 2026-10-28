#!/usr/bin/env python3
"""Figures for the week-1 deck (01_why_real_time.md).

    python3 rt_figs.py        # writes rt_patriot.svg, rt_converge.svg, rt_tails.svg here
"""
import math
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, box, line, poly, rect, save, svg, text

HERE = Path(__file__).resolve().parent

TICK_ERR_S = 0.000000095367431640625  # 0.1 chopped to the Patriot's 24-bit register (GAO/IMTEC-92-26)
GAO_HOURS = [0, 1, 8, 20, 48, 72, 100]


def drift_s(hours):
    return hours * 3600 * 10 * TICK_ERR_S


def patriot():
    x0, x1, y0, y1 = 110, 1080, 380, 60
    sx = lambda h: x0 + (x1 - x0) * h / 100
    sy = lambda s: y0 - (y0 - y1) * s / 0.36
    body = [line(x0, y0, x1, y0, MUTED, 2), line(x0, y0, x0, y1, MUTED, 2)]
    for h in (0, 20, 40, 60, 80, 100):
        body += [line(sx(h), y0, sx(h), y0 + 8, MUTED), text(sx(h), y0 + 32, str(h), 18, 400, MUTED, "middle")]
    for s in (0, 0.1, 0.2, 0.3):
        body += [line(x0 - 8, sy(s), x0, sy(s), MUTED), text(x0 - 14, sy(s) + 6, f"{s:.1f}", 18, 400, MUTED, "end")]
    body.append(text((x0 + x1) / 2, y0 + 66, "hours since the battery was switched on", 20, 400, MUTED, "middle"))
    body.append(text(x0, y1 - 24, "clock error (s)", 20, 400, MUTED))
    body.append(poly([(sx(0), sy(0)), (sx(100), sy(drift_s(100)))], C["c5"], 4))
    for h in GAO_HOURS:
        body.append(f'<circle cx="{sx(h):.1f}" cy="{sy(drift_s(h)):.1f}" r="6" fill="{C["c5"]}"/>')
    d100 = drift_s(100)
    body.append(text(sx(100) - 14, sy(d100) - 18, f"Dhahran, ≈ 100 h: {d100:.2f} s", 22, 700, C["c5"], "end"))
    body.append(text(sx(100) - 14, sy(0.06), "a Scud covers ≈ 1,676 m/s × 0.34 s:", 19, 400, INK, "end"))
    body.append(text(sx(100) - 14, sy(0.06) + 26, "over half a kilometer", 19, 700, INK, "end"))
    body.append(text(sx(3), sy(0.27), "0.1 s in a 24-bit register:", 20, 700, INK))
    body.append(text(sx(3), sy(0.27) + 28, "0.000000095 s lost on every tick", 20, 400, INK))
    return svg(1130, 470, body)


def converge():
    body = []
    srcs = [("Digital systems", "setup/hold: late = wrong value", "c2"),
            ("Computation structures", "registers, IRQs, superloops", "c6"),
            ("Control systems", "the loop assumes a constant T", "c3")]
    for i, (name, sub, col) in enumerate(srcs):
        y = 30 + i * 120
        body.append(box(30, y, 400, 90, name, col, 22, sub))
        body.append(line(440, y + 45, 640, 205, MUTED, 3, arrow=True))
    body.append(rect(650, 150, 220, 110, T["c5"], C["c5"], 3, 55))
    body.append(text(760, 220, "when", 40, 700, C["c5"], "middle"))
    body.append(line(880, 205, 960, 205, MUTED, 3, arrow=True))
    body.append(text(975, 196, "this course:", 22, 400, INK))
    body.append(text(975, 228, "make “when” a guarantee", 22, 700, INK))
    return svg(1340, 400, body)


def tails():
    xs = [i * 0.05 for i in range(0, 281)]  # 0..14 ms
    norm = lambda x, m, s: math.exp(-0.5 * ((x - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))
    tail = lambda x: (math.exp(-(x - 5) / 2.0) / 2.0) if x >= 5 else 0.0
    fast = [0.92 * norm(x, 4.4, 0.5) + 0.08 * tail(x) for x in xs]
    mean_fast = sum(x * p for x, p in zip(xs, fast)) / sum(fast)
    steady = [norm(x, mean_fast, 0.35) for x in xs]
    x0, x1, y0, y1, dl = 110, 1180, 390, 60, 10
    sx = lambda x: x0 + (x1 - x0) * x / 14
    sy = lambda p: y0 - (y0 - y1) * (math.log10(max(p, 1e-5)) + 5) / 5
    body = [line(x0, y0, x1, y0), line(x0, y0, x0, y1)]
    for ms in range(0, 15, 2):
        body += [line(sx(ms), y0, sx(ms), y0 + 8), text(sx(ms), y0 + 30, str(ms), 18, 400, MUTED, "middle")]
    for e, lab in ((0, "1"), (-2, "10⁻²"), (-4, "10⁻⁴")):
        body.append(text(x0 - 12, sy(10 ** e) + 6, lab, 18, 400, MUTED, "end"))
    body.append(text((x0 + x1) / 2, y0 + 62, "latency (ms)", 20, 400, MUTED, "middle"))
    body.append(text(x0, y1 - 24, "how often (log scale)", 20, 400, MUTED))
    for data, col, label, ly in ((steady, "c3", "steady", 0), (fast, "c1", "fast on average", 1)):
        pts = [(sx(x), sy(p)) for x, p in zip(xs, data) if p > 1e-5]
        body.append(poly(pts, C[col], 4))
        body.append(text(sx(0.3), y1 + 30 + ly * 32, f"— {label}", 22, 700, C[col]))
    body.append(text(sx(0.3), y1 + 94, f"same average: {mean_fast:.1f} ms", 20, 400, INK))
    body.append(line(sx(dl), y1, sx(dl), y0, C["c5"], 4))
    body.append(text(sx(dl) + 10, y1 + 24, "deadline", 22, 700, C["c5"]))
    body.append(text(sx(11.8), sy(0.03), "the tail", 22, 700, C["c1"], "middle"))
    return svg(1230, 480, body)


if __name__ == "__main__":
    assert abs(drift_s(100) - 0.3433) < 0.0005, "GAO: 0.3433 s after 100 h"
    for name, fig in (("rt_patriot.svg", patriot), ("rt_converge.svg", converge), ("rt_tails.svg", tails)):
        save(HERE, name, fig())
    print("rt_patriot.svg rt_converge.svg rt_tails.svg")
