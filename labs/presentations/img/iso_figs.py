#!/usr/bin/env python3
"""Figures for the week-10 deck (10_deadline_isolation.md).

    python3 iso_figs.py       # writes iso_layers.svg here
"""
from pathlib import Path

from figlib import C, INK, MUTED, T, line, rect, save, svg, text

HERE = Path(__file__).resolve().parent

LAYERS = [("IRQ affinity", "device interrupts", "c1"),
          ("isolcpus · nohz_full · rcu_nocbs", "other tasks, ticks, RCU", "c6"),
          ("affinity (taskset)", "where the loop may run", "c2"),
          ("SCHED_DEADLINE", "CPU time, by contract", "c3")]


def layers():
    cx, cy, body = 440, 310, []
    for i, (name, stops, col) in enumerate(LAYERS):
        w, h = 820 - i * 150, 580 - i * 130
        x, y = cx - w / 2, cy - h / 2
        body.append(rect(x, y, w, h, T[col] if i == len(LAYERS) - 1 else "none", C[col], 4, 26))
        body.append(text(x + 18, y + 30, name, 22, 700, C[col]))
        body.append(text(x + 18, y + 56, f"stops: {stops}", 19, 400, MUTED))
    body.append(text(cx, cy + 46, "core 3: the pump loop", 26, 700, INK, "middle"))
    body.append(line(1010, 200, cx + 120, cy + 30, C["c5"], 3, "8 6", arrow=True))
    body.append(text(1250, 160, "shared cache and memory bus:", 22, 700, C["c5"], "end"))
    body.append(text(1250, 188, "no layer stops it", 22, 700, C["c5"], "end"))
    return svg(1270, 620, body)


if __name__ == "__main__":
    save(HERE, "iso_layers.svg", layers())
    print("iso_layers.svg")
