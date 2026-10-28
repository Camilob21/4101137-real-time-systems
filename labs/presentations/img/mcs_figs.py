#!/usr/bin/env python3
"""Figures for the week-11 deck (11_kickoff.md).

    python3 mcs_figs.py       # writes mcs_hub.svg, mcs_watchdog.svg here
"""
from pathlib import Path

from figlib import C, INK, MUTED, T, box, line, poly, rect, save, svg, text

HERE = Path(__file__).resolve().parent


def hub():
    body = [rect(300, 30, 640, 420, "#f8fafc", MUTED, 3, 20), text(320, 64, "SoilSense Hub · Raspberry Pi 4, PREEMPT_RT", 21, 700, INK)]
    body.append(rect(320, 90, 600, 150, T["c5"], C["c5"], 2, 14))
    body.append(text(340, 122, "hard · isolated CPU 3", 20, 700, C["c5"]))
    body.append(box(340, 140, 260, 80, "pump loop", "c5", 21, "SCHED_DEADLINE"))
    body.append(box(640, 140, 260, 80, "interlock", "c5", 21, "stops the pump"))
    body.append(rect(320, 260, 600, 170, T["c2"], C["c2"], 2, 14))
    body.append(text(340, 292, "firm and soft · CPUs 0–2", 20, 700, C["c2"]))
    body.append(box(340, 310, 170, 90, "GUI", "c7", 21, "soft"))
    body.append(box(530, 310, 170, 90, "routing", "c3", 21, "firm"))
    body.append(box(720, 310, 180, 90, "CAN IRQ", "c8", 21, "thread"))
    body.append(box(30, 290, 220, 110, "Control nodes", "c6", 22, "ESP32-S3, over CAN"))
    body.append(poly([(250, 345), (280, 345), (280, 418), (810, 418), (810, 402)], C["c5"], 4, arrow=True))
    body.append(poly([(810, 310), (810, 250), (770, 220)], C["c5"], 4))
    body.append(box(1000, 150, 200, 80, "pump", "c1", 22))
    body.append(line(900, 180, 1000, 190, C["c5"], 4, arrow=True))
    body.append(box(30, 110, 220, 90, "pressure sensor", "c4", 20))
    body.append(line(250, 155, 340, 165, C["c5"], 4, arrow=True))
    body.append(text(620, 490, "red: the two hard paths · sensor → interlock → pump · node e-stop → CAN → pump stop",
                     19, 700, C["c5"], "middle"))
    return svg(1230, 510, body)


def watchdog():
    body = [box(40, 60, 300, 100, "control loop", "c3", 24, "a healthy cycle"),
            box(520, 60, 300, 100, "hardware watchdog", "c6", 24, "counts down on its own"),
            box(520, 300, 300, 100, "safe state", "c5", 24, "valve closed (spring)"),
            box(940, 300, 220, 100, "reboot", "c2", 24)]
    body += [line(340, 110, 520, 110, INK, 3, arrow=True), text(430, 98, "kick", 22, 700, INK, "middle"),
             line(670, 160, 670, 300, C["c5"], 4, arrow=True), text(690, 240, "no kick in time: bite", 22, 700, C["c5"]),
             line(820, 350, 940, 350, INK, 3, arrow=True)]
    body.append(rect(40, 260, 360, 140, "#f8fafc", MUTED, 2, 12, "8 6"))
    body.append(text(220, 300, "kicking from a timer ISR", 21, 700, MUTED, "middle"))
    body.append(text(220, 332, "keeps kicking while", 20, 400, INK, "middle"))
    body.append(text(220, 360, "the application is dead", 20, 400, INK, "middle"))
    body.append(line(60, 280, 380, 385, C["c5"], 4))
    return svg(1200, 430, body)


if __name__ == "__main__":
    save(HERE, "mcs_hub.svg", hub())
    save(HERE, "mcs_watchdog.svg", watchdog())
    print("mcs_hub.svg mcs_watchdog.svg")
