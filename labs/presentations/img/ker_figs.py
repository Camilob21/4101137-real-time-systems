#!/usr/bin/env python3
"""Figures for the week-3 deck (03_scheduler.md).

    python3 ker_figs.py       # writes ker_port.svg, ker_states.svg, ker_chain.svg here
"""
from pathlib import Path

from figlib import C, INK, MUTED, T, box, line, rect, save, svg, text
from lat_figs import chain

HERE = Path(__file__).resolve().parent


def port():
    body = [box(440, 150, 300, 110, "main.c", "c6", 30, "0 lines changed"),
            box(20, 40, 380, 100, "nucleo_l476rg.overlay", "c2", 18, "&gpiob 3, &gpioa 8, LD2 …"),
            box(20, 270, 380, 100, "esp32s3_devkitc_…procpu.overlay", "c7", 18, "&gpio0 4…17, valve_out GPIO21"),
            box(800, 40, 300, 100, "NUCLEO-L476RG", "c2", 22, "Cortex-M4, 80 MHz"),
            box(800, 270, 300, 100, "ESP32-S3", "c7", 22, "Xtensa LX7, 240 MHz")]
    body += [line(390, 90, 800, 90, MUTED, 3, arrow=True), line(390, 320, 800, 320, MUTED, 3, arrow=True),
             line(590, 150, 620, 128, MUTED, 2, arrow=True), line(590, 260, 620, 282, MUTED, 2, arrow=True)]
    body.append(text(590, 420, "the port is data, not code: one overlay per board", 24, 700, INK, "middle"))
    return svg(1140, 440, body)


def states():
    body = [box(40, 110, 240, 100, "Ready", "c7", 28, "wants the CPU"),
            box(560, 110, 240, 100, "Running", "c3", 28, "has the CPU"),
            box(300, 340, 240, 100, "Blocked", "c2", 28, "waits: costs no CPU")]
    body += [line(280, 140, 560, 140, INK, 3, arrow=True), text(420, 128, "highest priority Ready", 18, 700, INK, "middle"),
             line(560, 182, 280, 182, INK, 3, arrow=True), text(420, 206, "preempted", 18, 700, INK, "middle"),
             line(640, 210, 500, 340, INK, 3, arrow=True), text(590, 300, "k_msgq_get, k_sleep", 18, 700, INK),
             line(340, 340, 200, 210, INK, 3, arrow=True), text(250, 300, "data, timeout", 18, 700, INK, "end")]
    body.append(rect(860, 110, 300, 140, "#f8fafc", MUTED, 2, 12, "8 6"))
    body.append(text(1010, 160, "the superloop", 22, 700, MUTED, "middle"))
    body.append(text(1010, 192, "has no Blocked state:", 20, 400, INK, "middle"))
    body.append(text(1010, 222, "it polls, always Running", 20, 400, INK, "middle"))
    body.append(text(600, 50, "the scheduler's one rule: the highest-priority Ready thread runs", 24, 700, INK, "middle"))
    return svg(1200, 460, body)


if __name__ == "__main__":
    save(HERE, "ker_port.svg", port())
    save(HERE, "ker_states.svg", states())
    save(HERE, "ker_chain.svg", chain(kernel=True))
    print("ker_port.svg ker_states.svg ker_chain.svg")
