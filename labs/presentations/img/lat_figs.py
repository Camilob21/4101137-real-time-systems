#!/usr/bin/env python3
"""Figures for the week-2 deck (02_vocabulary.md); chain() is reused by week 3.

    python3 lat_figs.py       # writes lat_value.svg, lat_chain.svg here
"""
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, line, poly, rect, save, svg, text

HERE = Path(__file__).resolve().parent


def value():
    """Buttazzo §2.2: the value of a result finished at time t, per deadline type."""
    panels = [("Hard", "c5", "a late result does damage", "e-stop: a hose bursts",
               [(0, 1), (0.6, 1), (0.6, -0.8), (1, -0.8)]),
              ("Firm", "c6", "a late result is worthless", "console reply: stale",
               [(0, 1), (0.6, 1), (0.6, 0), (1, 0)]),
              ("Soft", "c3", "a late result is worth less", "telemetry: a late point",
               [(0, 1), (0.6, 1), (0.75, 0.45), (1, 0.15)])]
    body, w, gap = [], 380, 40
    for i, (name, col, gist, node, curve) in enumerate(panels):
        x0 = 40 + i * (w + gap)
        y_zero, y_one = 210, 90
        sx = lambda t: x0 + 30 + (w - 50) * t
        sy = lambda v: y_zero - (y_zero - y_one) * v
        body.append(text(x0 + w / 2, 40, name, 30, 700, C[col], "middle"))
        body.append(line(sx(0), y_zero, sx(1), y_zero, MUTED, 2, arrow=True))
        body.append(line(sx(0), sy(-1), sx(0), sy(1.25), MUTED, 2, arrow=True))
        body.append(text(sx(0) - 8, sy(1.25) + 4, "v", 20, 700, MUTED, "end"))
        body.append(text(sx(1), y_zero + 26, "t", 20, 700, MUTED, "end"))
        body.append(line(sx(0.6), sy(1.2), sx(0.6), sy(-1), C["c5"], 2, "6 5"))
        body.append(text(sx(0.6), sy(-1) + 22, "deadline", 17, 700, C["c5"], "middle"))
        body.append(poly([(sx(t), sy(v)) for t, v in curve], C[col], 5))
        body.append(text(x0 + w / 2, 395, gist, 20, 700, INK, "middle"))
        body.append(text(x0 + w / 2, 425, node, 19, 400, MUTED, "middle"))
    return svg(40 + 3 * w + 2 * gap + 20, 445, body)


LINKS = [("1", "event → IRQ", "input sync, cycles", "c2"),
         ("2", "IRQ latency", "12 cycles, if unmasked", "c2"),
         ("3", "ISR body", "capture + flag, µs", "c2"),
         ("4", "hand-off wait", "the loop must come round", "c5"),
         ("5", "service", "handler runs, valve moves", "c2")]


def chain(kernel=False):
    body, w, gap, y = [], 250, 26, 70
    for i, (n, name, sub, col) in enumerate(LINKS):
        x = 30 + i * (w + gap)
        if kernel and n == "4":
            col, name, sub = "c3", "preemption", "bounded by the switch"
        body.append(rect(x, y, w, 120, T[col], C[col], 3 if n == "4" else 2, 12))
        body.append(text(x + 16, y + 30, n, 22, 700, C[col]))
        body.append(text(x + w / 2, y + 66, name, 24, 700, C[col], "middle"))
        body.append(text(x + w / 2, y + 98, sub, 18, 400, INK, "middle"))
        if i < len(LINKS) - 1:
            body.append(line(x + w + 2, y + 55, x + w + gap - 4, y + 55, MUTED, 3, arrow=True))
    x4 = 30 + 3 * (w + gap)
    if kernel:
        body.append(text(x4 + w / 2, y + 160, "the slowest task no longer counts", 22, 700, C["c3"], "middle"))
    else:
        body.append(text(x4 + w / 2, y + 160, "bounded by the longest loop pass", 22, 700, C["c5"], "middle"))
        body.append(text(x4 + w / 2, y + 190, "the villain", 22, 400, C["c5"], "middle"))
    body.append(text(30, 40, "fixed delays add latency · variable delays add jitter", 24, 700, MUTED))
    return svg(30 + 5 * w + 4 * gap + 30, 280, body)


if __name__ == "__main__":
    save(HERE, "lat_value.svg", value())
    save(HERE, "lat_chain.svg", chain())
    print("lat_value.svg lat_chain.svg")
