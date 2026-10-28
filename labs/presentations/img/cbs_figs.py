#!/usr/bin/env python3
"""Figures for the week-10 deck (10_deadline_isolation.md).

    python3 cbs_figs.py       # writes cbs_hog.svg here

One CPU, a 10 ms pump loop needing 1.1 ms per period, and a busy-looping hog that
starts at 3 ms. SCHED_DEADLINE tasks run before any SCHED_FIFO task (Linux
scheduling classes); the reservation is 2 ms every 10 ms.
"""
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, line, poly, rect, save, svg, text

HERE = Path(__file__).resolve().parent

PERIOD, C_LOOP, RUNTIME, HOG_START, HORIZON = 10.0, 1.1, 2.0, 3.0, 40.0
X0, SCALE = 280, 22


def sx(ms):
    return X0 + ms * SCALE


def lane(body, y, name, col, segments):
    body.append(text(X0 - 14, y + 26, name, 19, 700, C[col], "end"))
    body.append(line(sx(0), y + 34, sx(HORIZON), y + 34, GRID, 2))
    for a, b in segments:
        body.append(rect(sx(a), y + 6, (b - a) * SCALE, 28, T[col], C[col]))


def axis(body, y):
    for ms in range(0, int(HORIZON) + 1, 10):
        body.append(text(sx(ms), y, f"{ms} ms", 16, 400, MUTED, "middle"))


def hog():
    releases = [k * PERIOD for k in range(int(HORIZON // PERIOD))]
    body, y = [], 20

    body.append(text(X0, y + 24, "loop at FIFO 90, hog at FIFO 95", 22, 700, INK))
    lane(body, y + 40, "pump loop", "c5", [(0, C_LOOP)])
    for t in releases[1:]:
        body.append(text(sx(t + 0.2), y + 68, "✕ miss", 18, 700, C["c5"]))
    lane(body, y + 84, "hog", "c7", [(HOG_START, HORIZON)])
    axis(body, y + 150)

    y += 190
    body.append(text(X0, y + 24, "loop at DEADLINE 2 ms / 10 ms, same hog", 22, 700, INK))
    lane(body, y + 40, "pump loop", "c5", [(t, t + C_LOOP) for t in releases])
    lane(body, y + 84, "hog", "c7", [(max(t + C_LOOP, HOG_START), t + PERIOD) for t in releases])
    by = y + 170
    budget = []
    for t in releases:
        budget += [(t, RUNTIME), (t + C_LOOP, RUNTIME - C_LOOP), (t + PERIOD, RUNTIME - C_LOOP)]
    body.append(text(X0 - 14, by + 6, "loop's budget", 19, 700, C["c6"], "end"))
    body.append(line(sx(0), by + 20, sx(HORIZON), by + 20, GRID, 2))
    body.append(poly([(sx(t), by + 20 - 22 * q) for t, q in budget], C["c6"], 3))
    axis(body, by + 52)
    return svg(sx(HORIZON) + 40, by + 70, body)


if __name__ == "__main__":
    save(HERE, "cbs_hog.svg", hog())
    print("cbs_hog.svg")
