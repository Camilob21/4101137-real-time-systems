# GreenField Technologies: Project Briefing

**Document type**: Project context and stakeholder guide

**Audience**: Firmware Engineers — Control Systems team (students)

---

## 1. The Company

**GreenField Technologies** is a fictional precision-agriculture startup for
small and mid-size farms (5–50 ha). Values: affordability, simplicity,
sustainability, resilience. Its first product, the **SoilSense** sensor network,
is already deployed on pilot farms reporting soil moisture and temperature.

**The new problem**: the data tells the farmer *when* to irrigate, but she still
opens valves by hand. She over-irrigates to be safe, or arrives late. GreenField
decided to close the loop: sensing → decision → **actuation**.

**Why this is a real-time problem**: a valve that closes late during an
overpressure bursts a hose; a flow control loop with jitter irrigates poorly; an
emergency stop has a deadline, not a suggestion. The deadlines are now physical.

## 2. The Products

### SoilSense Control (course modules 1–4)
ESP32-S3 + Zephyr irrigation controller. Its tasks embody the course taxonomy:

| Task | Type | Example requirement |
|------|------|---------------------|
| Flow/pressure control loop (PWM to valve/pump) | **Hard** | period 10 ms, deadline = period |
| Overpressure emergency stop | **Hard** | response < 5 ms |
| Sensor sampling | **Hard** | 1 kHz, bounded jitter |
| Telemetry to the Hub | **Soft** | delays degrade, don't break |
| Command console | **Firm** | a late response is worthless, but harmless |

*(Numbers are references; they're fixed and justified in each module's ADRs.)*

### SoilSense Hub (final project, weeks 11–14)
Gateway on a Linux SBC (PREEMPT_RT), shared per group. The Hub is **not just a
supervisor**: it's a mixed-criticality system with hard requirements of its own,
and its real-time design is the heart of the final project. In the same box coexist:

- **Local hard control**: the pump station's pressure loop and its safety
  interlock (`SCHED_FIFO`/`SCHED_DEADLINE`, CPU isolation).
- **Local GUI** (touchscreen — e.g. LVGL or a web HMI) for field operation.
- **Data routing**: telemetry and alarms from the Control nodes arrive over a
  **CAN bus**, the field bus of farm machinery (ISOBUS, ISO 11783, is CAN); the Hub
  forwards them to the remote dashboard/cloud and sends commands back.

The CAN bus makes one hard requirement cross three computers: *when a Control node
trips its overpressure e-stop, the Hub shall stop the pump within 20 ms*. Its budget
adds the node's response time (detection on one core, the hand-off to the core
that owns the bus), the frame's response time on the bus (CAN arbitrates
by priority, so the bus has its own RTA), and the Hub's wake-up latency.

**The design challenge**: prove the hard loop meets its deadlines *while* the GUI
renders and the routing takes traffic bursts — with evidence (`cyclictest` and
traces under synthetic load). GreenField builds those two with an AI agent, from
a spec the team writes, so the Hub runs code nobody on the team typed. Plus the
partitioning ADR: which functions live in
Linux and which on the MCU (ESP32-S3), and why.

**Safety requirement (explicit deliverable)**: the system declares its **safe
state** (failure ⇒ valve closed) and protects it with a **watchdog** — if the
control loop dies, the hardware reaches the safe state on its own. It's the
design answer to Edwin's question ("what if the Hub goes down with a valve open?").

## 3. Your Role and Team

- **Role**: Firmware Engineer, Control Systems team.
- **Modules 1–4**: in pairs, one ESP32-S3 kit per pair.
- **Modules 5–6**: pairs merge into groups (4–6) sharing the Hub's SBC.
- **Mentor**: Eng. Samuel Cifuentes (Senior Architect). Reviews ADRs and timing
  evidence. Signature phrase: *"show me the trace"*.

### Stakeholders

| Stakeholder | Role | Cares about | Typical question |
|-------------|------|-------------|------------------|
| **Samuel** | Senior Architect | Correctness, schedulability analysis | "What's the worst case, and how did you measure it?" |
| **Gustavo** | Product Owner | Cost, customer value | "Why does a real-time kernel make the product more expensive?" |
| **Edwin** | Field Operations | Reliability, failures | "What happens if the Hub goes down while a valve is open?" |
| **Edward** | Security | Attack surface | "Can a malicious remote command violate a deadline?" |
| **Daniela** | Pilot customer | Usability, ROI | "Does the screen tell me what's going on without calling support?" |

## 4. Project Phases

| Phase | Weeks | What the team delivers |
|---|---|---|
| 1. Prototype and baseline | 1–5 | The node as a superloop and its jitter baseline; the same node on threads, A/B against it; the first traces |
| 2. Guarantees | 6–7 | Schedulability analysis and RTA of the node's task set; priority inversion reproduced and fixed; the design review (week 7) |
| 3. Two cores | 8 | The hard loop alone on the S3's second core, judged by its tail and built together into the project's node; FreeRTOS as the alternative a customer may demand |
| 4. The Hub | 9–14 | RT Linux measured and isolated; the Hub designed, built and linked to the nodes over CAN; two checkpoints and demo day |

## 5. Documentation Standards

ADRs before implementing, decisions justified with numbers, explicit trade-offs.
Additionally, in this project every timing requirement is declared with an ID
(`REQ-…`, one EARS-style sentence: condition → response → deadline; hard/firm/soft
type, period, deadline) and **verified with measured evidence** (latency/jitter
table or trace) — all of it lives in the **RET** (Timing Evidence Report, template
in [templates/ret.md](templates/ret.md)), the team's living document.
