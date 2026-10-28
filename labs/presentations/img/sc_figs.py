#!/usr/bin/env python3
"""Figures for the week-6 deck (06_schedulability.md). Standard library only.

    python3 sc_figs.py        # writes sc_fig413.svg and sc_bounds.svg here

The schedules are simulated, not drawn: changing TASKS redraws Fig. 4.13 for any set.
"""
import math
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, svg, text

HERE = Path(__file__).resolve().parent

TASKS = [("τ1", 2, 5, "c6"), ("τ2", 4, 7, "c7")]  # Buttazzo Fig. 4.13: (name, C, T, color)


def simulate(tasks, policy, horizon):
    """Unit-step schedule: (who runs each unit, deadline misses, preemptions per task).
    Late jobs keep running, as on a real kernel."""
    jobs, timeline, misses, running = [], [], [], None
    preempted = [0] * len(tasks)
    for t in range(horizon):
        for i, (_, c, p, _) in enumerate(tasks):
            if t % p == 0:
                jobs.append({"task": i, "left": c, "deadline": t + p})
        ready = [j for j in jobs if j["left"] > 0]
        if not ready:
            timeline.append(None)
            running = None
            continue
        if policy == "RM":
            job = min(ready, key=lambda j: (tasks[j["task"]][2], j["task"], j["deadline"]))
        else:
            d = min(j["deadline"] for j in ready)
            job = running if running in ready and running["deadline"] == d else \
                min((j for j in ready if j["deadline"] == d), key=lambda j: j["task"])
        if running is not None and running is not job and running["left"] > 0:
            preempted[running["task"]] += 1
        job["left"] -= 1
        timeline.append(job["task"])
        running = job
        for j in jobs:
            if j["left"] > 0 and j["deadline"] == t + 1:
                misses.append((j["task"], t + 1))
    return timeline, misses, preempted


def fig413():
    horizon = math.lcm(*(p for _, _, p, _ in TASKS))
    x0, unit, lane, w = 130, 32, 46, 0
    w = x0 + unit * horizon + 40
    body, y = [], 20
    for policy in ("RM", "EDF"):
        tl, misses, pre = simulate(TASKS, policy, horizon)
        n_pre = pre[1]
        body.append(text(20, y + 24, policy, 28, 700))
        body.append(text(x0, y + 24, f"τ2 preempted {n_pre}×"
                         + (f" · misses its deadline at t = {misses[0][1]}" if misses else " · no misses"),
                         22, 700 if misses else 400, C["c5"] if misses else MUTED))
        for i, (name, c, p, col) in enumerate(TASKS):
            ly = y + 40 + i * lane
            body.append(text(x0 - 16, ly + 30, name, 24, 700, C[col], "end"))
            body.append(f'<line x1="{x0}" y1="{ly + 36}" x2="{x0 + unit * horizon}" y2="{ly + 36}" stroke="{GRID}" stroke-width="2"/>')
            for t, who in enumerate(tl):
                if who == i:
                    body.append(f'<rect x="{x0 + t * unit}" y="{ly + 8}" width="{unit}" height="28" fill="{T[col]}" stroke="{C[col]}" stroke-width="2"/>')
            for r in range(0, horizon + 1, p):
                rx = x0 + r * unit
                body.append(f'<path d="M{rx} {ly + 36} L{rx} {ly + 2}" stroke="{MUTED}" stroke-width="2"/>'
                            f'<path d="M{rx - 5} {ly + 10} L{rx} {ly + 2} L{rx + 5} {ly + 10}" fill="none" stroke="{MUTED}" stroke-width="2"/>')
        for task, t in misses:
            mx, my = x0 + t * unit, y + 40 + task * lane + 22
            body.append(f'<circle cx="{mx}" cy="{my}" r="17" fill="none" stroke="{C["c5"]}" stroke-width="4"/>')
        ay = y + 40 + len(TASKS) * lane + 6
        for t in range(0, horizon + 1, 5):
            body.append(text(x0 + t * unit, ay + 20, str(t), 18, 400, MUTED, "middle"))
        y = ay + 50
    body.append(text(x0, y, "↑ release = deadline of the previous job · late jobs keep running, as on the board", 18, 400, MUTED))
    return svg(w, y + 12, body)


def bounds():
    x0, x1, w = 80, 1180, 1280
    sx = lambda u: x0 + (x1 - x0) * u / 1.1
    u_fig = sum(c / p for _, c, p, _ in TASKS)
    ll2 = 2 * (2 ** 0.5 - 1)
    body = []
    rows = [("EDF", [(0, 1, "c3", "guaranteed: U ≤ 1 is exact"), (1, 1.1, "c5", "overload")]),
            ("RM", [(0, math.log(2), "c3", "guaranteed, any n"), (math.log(2), 1, "c7", "maybe: run RTA"),
                    (1, 1.1, "c5", "overload")])]
    for k, (name, spans) in enumerate(rows):
        y = 40 + k * 110
        body.append(text(20, y + 40, name, 26, 700))
        for a, b, col, label in spans:
            body.append(f'<rect x="{sx(a)}" y="{y}" width="{sx(b) - sx(a)}" height="60" fill="{T[col]}" stroke="{C[col]}" stroke-width="2"/>')
            body.append(text((sx(a) + sx(b)) / 2, y + 39, label, 22 if b - a > 0.2 else 18, 700, C[col], "middle"))
    y = 270
    body.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{MUTED}" stroke-width="2"/>')
    for u in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        body.append(f'<line x1="{sx(u)}" y1="{y - 6}" x2="{sx(u)}" y2="{y + 6}" stroke="{MUTED}" stroke-width="2"/>')
        body.append(text(sx(u), y + 30, f"{u:.1f}", 20, 400, MUTED, "middle"))
    for u, label, dy, anchor in ((math.log(2), "ln 2 ≈ 0.69 (n → ∞)", 66, "end"), (ll2, "n = 2: 0.83", 96, "middle"),
                                 (u_fig, f"Fig. 4.13: {u_fig:.2f}", 126, "middle")):
        body.append(f'<line x1="{sx(u)}" y1="{y - 54}" x2="{sx(u)}" y2="{y + dy - 22}" stroke="{INK}" stroke-width="2" stroke-dasharray="6 5"/>')
        body.append(text(sx(u) + (8 if anchor == "end" else 0), y + dy, label, 21, 700, INK, anchor))
    body.append(text(x1, y + 30, "U", 22, 700, MUTED, "end"))
    return svg(w, y + 140, body)


if __name__ == "__main__":
    _, rm_miss, rm_pre = simulate(TASKS, "RM", 35)
    _, edf_miss, edf_pre = simulate(TASKS, "EDF", 35)
    assert rm_miss == [(1, 7)] and not edf_miss, "Fig. 4.13: RM misses at t = 7, EDF never"
    assert rm_pre[1] == 5 and edf_pre[1] == 1, "book: τ2 preempted 5 times under RM, once under EDF"
    (HERE / "sc_fig413.svg").write_text(fig413())
    (HERE / "sc_bounds.svg").write_text(bounds())
    print("sc_fig413.svg sc_bounds.svg")
