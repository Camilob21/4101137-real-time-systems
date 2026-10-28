# Session format

This course follows the shared course standard,
[course-kit/STANDARD.md](https://github.com/saacifuentesmu/course-kit/blob/main/STANDARD.md):
a 40-minute talk (a Marp deck whose speaker notes are the script) and a 2-hour lab
each week, plus an SOP only for heavy bring-ups. [`coursekit.toml`](coursekit.toml)
maps this repository's files to the standard's document types;
`python3 ../course-kit/tools/coursekit.py lint .` checks them.

What this course fixes on top of the standard:

| | This course |
|---|---|
| Course box in every lab | **What about FreeRTOS?** — 3–5 lines: the equivalent API, and when that option wins |
| Living record | **RET — Timing Evidence Report** ([templates/ret.md](templates/ret.md)): updated weekly, handed in at the workshop (week 7) and at the close |
| House rule | *"Show me the trace"*: every timing claim cites a measurement and its instrument |
| Deck accent | `#0d9488` |

Templates: [lab](templates/lab.md) · [talk](templates/talk.md) ·
[SOP](templates/sop.md) · [RET](templates/ret.md)
