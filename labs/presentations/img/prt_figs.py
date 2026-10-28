#!/usr/bin/env python3
"""Figures for the week-9 deck (09_preempt_rt.md).

    python3 prt_figs.py       # writes prt_wakeup.svg here

Segment lengths are schematic: what can be preempted, not how long it takes.
"""
from pathlib import Path

from figlib import C, INK, MUTED, T, line, rect, save, svg, text

HERE = Path(__file__).resolve().parent

PATH = [("timer IRQ", 120, False, ""), ("other devices' IRQs", 220, True, "now threads"),
        ("a driver's spinlock", 220, True, "rtmutex + PI"), ("softirq", 150, True, "threaded"),
        ("scheduler", 140, False, ""), ("your thread", 150, False, "")]


def wakeup():
    body, x0 = [], 30
    for row, (title, rt) in enumerate((("Stock kernel: the shaded work can't be preempted", False),
                                       ("PREEMPT_RT: the same work, now in threads that priority can jump", True))):
        y = 30 + row * 190
        body.append(text(x0, y + 24, title, 22, 700, INK))
        x = x0
        for name, w, blocking, rt_note in PATH:
            if blocking and not rt:
                body.append(rect(x, y + 44, w, 80, T["c5"], C["c5"], 2, 8))
                body.append(text(x + w / 2, y + 90, name, 17, 700, C["c5"], "middle"))
            elif blocking and rt:
                body.append(rect(x, y + 44, w, 80, "#f8fafc", MUTED, 2, 8, "8 6"))
                body.append(text(x + w / 2, y + 80, name, 17, 400, MUTED, "middle"))
                body.append(text(x + w / 2, y + 106, rt_note, 17, 700, C["c3"], "middle"))
            else:
                col = "c3" if name == "your thread" else "c2"
                body.append(rect(x, y + 44, w, 80, T[col], C[col], 2, 8))
                body.append(text(x + w / 2, y + 90, name, 17, 700, C[col], "middle"))
            x += w + 8
        a, b = x0 + 128, x0 + 128 + 220 + 220 + 150 + 16
        col = "c3" if rt else "c5"
        msg = ("your thread outranks them: the wait becomes a switch" if rt
               else "latency = the longest of these, in code you didn't write")
        body.append(line(a, y + 140, b, y + 140, C[col], 3))
        body.append(text((a + b) / 2, y + 166, msg, 18, 700, C[col], "middle"))
    return svg(x0 + sum(w for _, w, _, _ in PATH) + 8 * len(PATH) + 20, 400, body)


if __name__ == "__main__":
    save(HERE, "prt_wakeup.svg", wakeup())
    print("prt_wakeup.svg")
