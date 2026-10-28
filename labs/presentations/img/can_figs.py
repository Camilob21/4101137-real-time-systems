#!/usr/bin/env python3
"""Figures for the week-12 deck (12_can.md). Standard library only.

    python3 can_figs.py       # writes can_arbitration.svg and can_budget.svg here
"""
from pathlib import Path

from figlib import C, GRID, INK, MUTED, T, svg, text

HERE = Path(__file__).resolve().parent

NODES = [("e-stop, node 1", 0x010, "c5"), ("telemetry, node 1", 0x012, "c3"), ("command, Hub", 0x100, "c2")]
BITRATE = 500_000
TAU_US = 1e6 / BITRATE


def frame_bits(data_bytes):
    """Worst-case bits of an 11-bit-ID frame with bit stuffing (Davis et al. 2007)."""
    return 55 + 10 * data_bytes


def can_response_us(c_us, b_max_us, hp=()):
    """Sufficient CAN RTA, no jitter: hp = [(C_k, T_k)] of higher-priority frames, in µs."""
    w = b_max_us
    while True:
        nxt = b_max_us + sum(-(-(w + TAU_US) // t) * c for c, t in hp)
        if nxt == w:
            return w + c_us
        w = nxt


def arbitration():
    x0, cell, row = 300, 64, 64
    bits = {name: [int(b) for b in f"{ident:011b}"] for name, ident, _ in NODES}
    lost = {}
    for i in range(11):
        alive = [n for n, *_ in NODES if n not in lost]
        bus = min(bits[n][i] for n in alive)
        for n in alive:
            if bits[n][i] != bus:
                lost[n] = i
    body = [text(x0 + 5.5 * cell, 30, "identifier bits, most significant first →", 20, 400, MUTED, "middle")]
    for i in range(11):
        body.append(text(x0 + i * cell + cell / 2, 62, str(10 - i), 18, 400, MUTED, "middle"))
    for r, (name, ident, col) in enumerate(NODES):
        y = 80 + r * row
        body.append(text(x0 - 16, y + 30, name, 20, 700, C[col], "end"))
        body.append(text(x0 - 16, y + 52, f"ID 0x{ident:03X}", 17, 400, MUTED, "end"))
        stop = lost.get(name, 11)
        for i in range(11):
            x = x0 + i * cell
            sending = i <= stop
            fill = T[col] if sending else "#f8fafc"
            stroke = C[col] if sending else GRID
            body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="48" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            body.append(text(x + cell / 2, y + 32, str(bits[name][i]) if sending else "·", 22, 700,
                             INK if sending else GRID, "middle"))
        if name in lost:
            x = x0 + lost[name] * cell
            body.append(f'<rect x="{x}" y="{y}" width="{cell}" height="48" fill="none" stroke="{INK}" stroke-width="4"/>')
            body.append(text(x0 + 11 * cell + 14, y + 32, f"loses at bit {10 - lost[name]}: listens", 19, 700, MUTED))
        else:
            body.append(text(x0 + 11 * cell + 14, y + 32, "wins: keeps sending", 19, 700, C[col]))
    y = 80 + len(NODES) * row + 16
    body.append(text(x0 - 16, y + 30, "the bus", 20, 700, INK, "end"))
    for i in range(11):
        alive = [n for n, *_ in NODES if lost.get(n, 11) >= i]
        level = min(bits[n][i] for n in alive)
        body.append(f'<rect x="{x0 + i * cell}" y="{y}" width="{cell}" height="48" fill="#e2e8f0" stroke="{MUTED}" stroke-width="2"/>')
        body.append(text(x0 + i * cell + cell / 2, y + 32, str(level), 22, 700, INK, "middle"))
    body.append(text(x0, y + 86, "0 is dominant: any node sending 0 pulls the bus to 0, so the lowest ID wins", 20, 400, INK))
    return svg(x0 + 11 * cell + 330, y + 104, body)


def budget():
    deadline_ms = 20
    node_ms = 1.0
    can_ms = can_response_us(frame_bits(1) * TAU_US, frame_bits(8) * TAU_US) / 1000
    x0, x1 = 60, 1220
    sx = lambda ms: x0 + (x1 - x0) * ms / deadline_ms
    y = 90
    body = [text(x0, 40, f"node trips → pump stops: {deadline_ms} ms", 24, 700, INK)]
    segs = [(0, node_ms, "c5"), (node_ms, node_ms + can_ms, "c7")]
    for a, b, col in segs:
        body.append(f'<rect x="{sx(a)}" y="{y}" width="{sx(b) - sx(a)}" height="70" fill="{T[col]}" stroke="{C[col]}" stroke-width="2"/>')
    rest = node_ms + can_ms
    body.append(f'<rect x="{sx(rest)}" y="{y}" width="{sx(deadline_ms) - sx(rest)}" height="70" fill="#f8fafc" '
                f'stroke="{MUTED}" stroke-width="2" stroke-dasharray="8 6"/>')
    body.append(text((sx(rest) + sx(deadline_ms)) / 2, y + 44,
                     f"{deadline_ms - rest:.1f} ms for the Hub path, actuation and margin: measure it", 22, 700, MUTED, "middle"))
    body.append(f'<line x1="{sx(deadline_ms)}" y1="{y - 20}" x2="{sx(deadline_ms)}" y2="{y + 90}" stroke="{C["c5"]}" stroke-width="4"/>')
    body.append(text(sx(deadline_ms), y - 28, "deadline", 20, 700, C["c5"], "end"))
    ly = y + 116
    lx = sx(rest) + 40
    for k, (mid, col, label) in enumerate((
            (node_ms / 2, "c5", f"node: ≈ {node_ms:.0f} ms to detect (ADR-005), plus the IPM hop (week 8)"),
            (node_ms + can_ms / 2, "c7", f"CAN: {can_ms * 1000:.0f} µs (1-byte frame, highest priority, 500 kbit/s)"))):
        yy = ly + k * 40
        body.append(f'<polyline points="{sx(mid)},{y + 70} {sx(mid)},{yy - 7} {lx - 8},{yy - 7}" fill="none" '
                    f'stroke="{C[col]}" stroke-width="2"/>')
        body.append(text(lx, yy, label, 21, 700, C[col]))
    return svg(1280, ly + 60, body)


if __name__ == "__main__":
    assert frame_bits(8) == 135 and frame_bits(0) == 55
    assert can_response_us(frame_bits(1) * TAU_US, frame_bits(8) * TAU_US) == 400
    (HERE / "can_arbitration.svg").write_text(arbitration())
    (HERE / "can_budget.svg").write_text(budget())
    print("can_arbitration.svg can_budget.svg")
