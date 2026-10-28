#!/usr/bin/env python3
"""Figures for the week-4 deck (04_ipc.md).

    python3 ipc_figs.py       # writes ipc_deferral.svg here

Durations are illustrative (µs); the shape, not the numbers, is the point.
"""
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, TASK, line, rect, save, svg, text

HERE = Path(__file__).resolve().parent

BATCH, SAMPLE, TICK = 40, 10, 15  # flow batch length, sampling length, tick arrival (µs)


def lanes(case):
    """Return [(lane, start, end)] for one placement of the flow batch."""
    if case == "isr":  # the tick ISR waits for the flow ISR to return
        return [("ISR", 0, BATCH), ("ISR", BATCH, BATCH + 1), ("sampling", BATCH + 1, BATCH + 1 + SAMPLE)]
    pre = [("ISR", 0, 2), ("flow batch", 2, TICK), ("ISR", TICK, TICK + 1)]
    left = BATCH - (TICK - 2)
    if case == "syswq":  # cooperative: sampling waits for the whole batch
        return pre + [("flow batch", TICK + 1, TICK + 1 + left), ("sampling", TICK + 1 + left, TICK + 1 + left + SAMPLE)]
    return pre + [("sampling", TICK + 1, TICK + 1 + SAMPLE), ("flow batch", TICK + 1 + SAMPLE, TICK + 1 + SAMPLE + left)]


def deferral():
    cases = [("isr", "batch inside the flow ISR"),
             ("syswq", "batch on the system workqueue (priority −1, cooperative)"),
             ("own", "batch on flow_wq (priority 5): sampling preempts it")]
    names = ["ISR", "flow batch", "sampling"]
    col = {"ISR": TASK["isr"], "flow batch": "c7", "sampling": TASK["sampling"]}
    x0, scale, lane_h, body, y = 190, 15, 34, [], 20
    for case, title in cases:
        segs = lanes(case)
        body.append(text(x0, y + 24, title, 22, 700, INK))
        for i, name in enumerate(names):
            ly = y + 40 + i * lane_h
            body.append(text(x0 - 14, ly + 23, name, 18, 700, C[col[name]], "end"))
            body.append(line(x0, ly + 30, x0 + 62 * scale, ly + 30, GRID, 2))
            for lane, a, b in segs:
                if lane == name:
                    body.append(rect(x0 + a * scale, ly + 4, (b - a) * scale, 26, T[col[name]], C[col[name]]))
        tick_x = x0 + TICK * scale
        top, bot = y + 34, y + 40 + 3 * lane_h
        body.append(line(tick_x, bot, tick_x, top, C["c5"], 3, arrow=True))
        start = next(a for lane, a, _ in segs if lane == "sampling")
        lat = start - TICK
        body.append(line(tick_x, bot + 10, x0 + start * scale, bot + 10, C["c5"], 3))
        body.append(text(x0 + start * scale + 10, bot + 16, f"tick → sampling: {lat} µs", 19, 700, C["c5"]))
        y = bot + 44
    body.append(text(x0, y, "↑ the 1 kHz tick arrives at the same moment in all three", 18, 400, MUTED))
    return svg(x0 + 62 * scale + 40, y + 14, body)


if __name__ == "__main__":
    save(HERE, "ipc_deferral.svg", deferral())
    print("ipc_deferral.svg")
