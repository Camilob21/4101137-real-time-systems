#!/usr/bin/env python3
"""Figures for the week-8 deck (08_freertos_multicore_wcet.md).

    python3 mc_figs.py        # writes mc_models.svg, mc_wcet.svg here
"""
import math
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, box, line, poly, rect, save, svg, text

HERE = Path(__file__).resolve().parent


def models():
    body = [text(290, 36, "Global: one queue, any core", 24, 700, INK, "middle"),
            text(910, 36, "Partitioned: one queue per core", 24, 700, INK, "middle")]
    body.append(rect(130, 70, 320, 70, T["c7"], C["c7"], 2, 10))
    body.append(text(290, 113, "ready queue: τ1 τ2 τ3 τ4", 22, 700, C["c7"], "middle"))
    for i, cpu in enumerate(("CPU 0", "CPU 1")):
        x = 80 + i * 240
        body.append(box(x, 230, 180, 80, cpu, "c2", 24))
        body.append(line(290, 140, x + 90, 230, MUTED, 3, arrow=True))
    body.append(text(290, 360, "tasks migrate: best average use,", 20, 400, INK, "middle"))
    body.append(text(290, 388, "per-core analysis no longer holds", 20, 400, INK, "middle"))
    body.append(text(290, 426, "ESP-IDF on the S3", 20, 700, MUTED, "middle"))
    for i, (cpu, q, col) in enumerate((("PROCPU", "node + load", "c7"), ("APPCPU", "hard loop alone", "c5"))):
        x = 690 + i * 260
        body.append(rect(x, 70, 200, 70, T[col], C[col], 2, 10))
        body.append(text(x + 100, 113, q, 21, 700, C[col], "middle"))
        body.append(box(x + 10, 230, 180, 80, cpu, "c2", 24))
        body.append(line(x + 100, 140, x + 100, 230, MUTED, 3, arrow=True))
    body.append(line(620, 60, 620, 440, GRID, 2))
    body.append(text(910, 360, "each core analyzed alone:", 20, 400, INK, "middle"))
    body.append(text(910, 388, "week 6 holds, core by core", 20, 400, INK, "middle"))
    body.append(text(910, 426, "Zephyr AMP on the S3: one image per core", 20, 700, MUTED, "middle"))
    return svg(1220, 450, body)


def wcet():
    """After Wilhelm et al. (2008), Fig. 1: what measurement and analysis each bound."""
    x0, x1, y0 = 80, 1180, 300
    sx = lambda u: x0 + (x1 - x0) * u
    xs = [i / 400 for i in range(0, 401)]
    dens = lambda u: max(u - 0.12, 0) ** 3 * math.exp(-max(u - 0.12, 0) / 0.05)
    top = max(dens(u) for u in xs)
    pts = [(sx(u), y0 - 200 * dens(u) / top) for u in xs if u < 0.56]
    body = [line(x0, y0, x1, y0, MUTED, 2, arrow=True), text(x1, y0 + 30, "execution time", 20, 400, MUTED, "end"),
            poly([(sx(0.12), y0)] + pts + [(pts[-1][0], y0)], C["c2"], 3, T["c2"])]
    marks = [(0.55, "observed max", "c2", "measurement"), (0.66, "high-water mark + margin", "c3", "industry default"),
             (0.74, "true WCET", "c5", "unknown"), (0.9, "static bound", "c6", "safe, pessimistic")]
    for k, (u, name, col, sub) in enumerate(marks):
        dash = "8 6" if name == "true WCET" else ""
        body.append(line(sx(u), y0 + 8, sx(u), 80, C[col], 3, dash))
        yl = 40 if k % 2 == 0 else 60
        body.append(text(sx(u), y0 + 58 + (k % 2) * 50, name, 20, 700, C[col], "middle"))
        body.append(text(sx(u), y0 + 82 + (k % 2) * 50, sub, 17, 400, MUTED, "middle"))
    body.append(line(sx(0.555), 70, sx(0.735), 70, C["c5"], 3))
    body.append(text(sx(0.645), 50, "measurement can miss this", 18, 700, C["c5"], "middle"))
    return svg(1240, 450, body)


if __name__ == "__main__":
    save(HERE, "mc_models.svg", models())
    save(HERE, "mc_wcet.svg", wcet())
    print("mc_models.svg mc_wcet.svg")
