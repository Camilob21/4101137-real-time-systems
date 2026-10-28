"""Drawing helpers shared by the deck figure scripts (*_figs.py). Standard library only.

Colors are the course-kit palette (theme/course.css): strong C[...] for strokes and text,
tints T[...] for fills. Task colors follow [palette] in coursekit.toml.
"""
from html import escape
from pathlib import Path

FONT = "Inter, 'Segoe UI', 'DejaVu Sans', Arial, sans-serif"
INK, MUTED, GRID, PANEL = "#0f172a", "#475569", "#cbd5e1", "#f8fafc"
C = {"c1": "#ea580c", "c2": "#2563eb", "c3": "#16a34a", "c4": "#0d9488",
     "c5": "#e11d48", "c6": "#7c3aed", "c7": "#d97706", "c8": "#db2777"}
T = {"c1": "#ffedd5", "c2": "#dbeafe", "c3": "#dcfce7", "c4": "#ccfbf1",
     "c5": "#ffe4e6", "c6": "#ede9fe", "c7": "#fef3c7", "c8": "#fce7f3"}
TASK = {"analyzer": "c1", "sampling": "c2", "telemetry": "c3", "trace": "c4",
        "control": "c5", "console": "c6", "display": "c7", "isr": "c8"}

ARROW_COLORS = {INK: "ink", MUTED: "muted", **{v: k for k, v in C.items()}}
DEFS = "<defs>" + "".join(
    f'<marker id="ar-{k}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
    f'<path d="M0 0 L10 5 L0 10 Z" fill="{v}"/></marker>' for v, k in ARROW_COLORS.items()) + "</defs>"


def _marker(stroke):
    return f' marker-end="url(#ar-{ARROW_COLORS.get(stroke, "muted")})"'


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" font-family="{FONT}">\n'
            + DEFS + "\n" + "\n".join(body) + "\n</svg>\n")


def text(x, y, s, size=20, weight=400, fill=INK, anchor="start", style=""):
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}"{st}>{escape(str(s), quote=False)}</text>')


def rect(x, y, w, h, fill, stroke, sw=2, rx=0, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def line(x1, y1, x2, y2, stroke=MUTED, sw=2, dash="", arrow=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = _marker(stroke) if arrow else ""
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{m}/>')


def poly(points, stroke=MUTED, sw=2, fill="none", dash="", arrow=False):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = _marker(stroke) if arrow else ""
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>'


def box(x, y, w, h, label, col, size=20, sub=""):
    """A tinted box with a centered label (and an optional smaller second line)."""
    out = [rect(x, y, w, h, T[col], C[col], 2, 10)]
    if sub:
        out.append(text(x + w / 2, y + h / 2 - 4, label, size, 700, C[col], "middle"))
        out.append(text(x + w / 2, y + h / 2 + size - 2, sub, size - 4, 400, INK, "middle"))
    else:
        out.append(text(x + w / 2, y + h / 2 + size / 3, label, size, 700, C[col], "middle"))
    return "\n".join(out)


def save(here, name, content):
    Path(here, name).write_text(content)
    return name
