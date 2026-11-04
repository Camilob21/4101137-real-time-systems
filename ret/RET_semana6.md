# RET — Semana 6: planificabilidad, tiempo de respuesta e inversión de prioridad

> Borrador para pegar en el RET del equipo. Todo lo que está entre `____` o `<...>` se
> llena con **tus** mediciones. Placa: ESP32-S3-DevKitC-1 (Zephyr, tick = 100 µs).
> Instrumento: Analog Discovery 2 (Logic, DIO0–DIO6) + consola + traza CTF (semana 5).

## Tabla de la semana (predicción antes de energizar, valor medido después)

| Medición | Predicción | Valor medido | Referencia | Evidencia |
|---|---|---|---|---|
| Fig. 4.13 bajo RM: ¿quién pierde y cuándo? | τ2, deadline t = 7 ms (termina en 8 ms) | τ2, job `__`, deadline `__` ms, termina `__` ms | libro: τ2 en t = 7 ms | `A1_RM_miss.png`, `A_RM_consola.txt` |
| Fig. 4.13 bajo EDF: pérdidas en 60 s | 0 | `__` (t = 60 s) | libro: ninguna, U ≈ 0.97 ≤ 1 | `A2_EDF_ok.png`, `A3_EDF_sin_trigger.png`, `A_EDF_consola.txt` |
| R máx. de control, sin contención | `__` µs | `__` µs | script RTA | `B1_sin_contencion.png` |
| R máx. de control con inversión (`k_sem`) | ≈ 15 000 µs + resto de la SC | `__` µs | — (eso es lo roto) | `B2_inversion_ksem.png` |
| R máx. de control con `k_mutex` | ≤ C + B + interferencia | `__` µs | ≤ C + B + interferencia | `B3_mutex_PI.png` |
| B: sección crítica más larga del hilo bajo | ≈ 3 000 µs | `__` µs | su pulso GPIO17 | `B3_mutex_PI.png` |
| `calib` CPU / duración, antes | ≈ 400 / ≈ 400 ms | `__` / `__` ms | gira: CPU = duración | `C3_calib_antes.png` |
| `calib` CPU / duración, después | ≈ 2 / ≈ 500 ms | `__` / `__` ms | | `C4_calib_despues.png`, `calib_cpu_traza.txt` |
| E-stop, detección → válvula baja, máx. de 5 disparos, antes / después | ≤ 11 / ≤ 0.05 ms | `__` / `__` ms | suma del camino (Task C) | `C1_estop_antes_*.png`, `C2_estop_despues_*.png` |

## §1 — Notas al conjunto de tareas

Medidos con el AD2 (ancho de pulso, máximo observado, sin contención):

| Tarea | Periodo | C medido | Instrumento |
|---|---|---|---|
| sampling (GPIO4) | 1 ms | `__` µs | GPIO + AD2 |
| control (GPIO5) | 10 ms | `__` µs | GPIO + AD2 (el pulso ahora incluye tomar/soltar el lock) |
| telemetría (GPIO7) | 1 s | `__` ms | GPIO + AD2 |

## §2 — ADRs

### ADR-002 — Política de exclusión mutua del nodo

**Contexto.** Control (prioridad 3, duro, 10 ms) y la consola (prioridad 9, firme)
comparten el estado del lazo (`setpoint_mv`, `integral_mv`, `estop`). Con un `k_sem`
de 1 como candado, una tarea media que no toca el candado (telemetría, prioridad 8)
puede desalojar a la consola mientras lo tiene: control quedó esperando
`__` µs (captura `B2`), es decir, `__` periodos de control perdidos.

**Decisión.** Todo recurso compartido entre prioridades se protege con `k_mutex`
(herencia de prioridad, PIP) y nunca con un semáforo binario. En el nodo:
`node_mutex` en `control_thread`, `set`, `clear` e `inv`.

**Justificación (con números).** Con `k_mutex`, R máx. de control = `__` µs
(captura `B3`), acotado por C + B + interferencia = `__` + `__` + `__` = `__` µs
(RTA, §4). B medido = `__` µs (ancho de GPIO17). Bajo PIP control puede bloquearse
a lo sumo una vez por la sección crítica de la consola (Teorema 7.2).

**Estado.** Aceptado e implementado (`firmware/node_w6`, `use_mutex = true` por defecto;
`lock sem` sólo existe para reproducir el fallo).

### ADR-005 — E-stop y `calib` arreglados en la fuente

**Contexto.**
- REQ-CONS-01: `calib` necesita ≈ 400 ms de CPU dentro de 1 s, a la prioridad más baja.
  Con las tareas de Daniela, las tareas por encima de la consola tienen U = `__`, así
  que le dejan (1 − U)·1 s = `__` ms < 400 ms: **no cabe** (antes).
- REQ-ESTOP-01: la detección ocurre en sampling, pero la válvula sólo cierra cuando
  control (siguiente múltiplo de 10 ms) pone duty = 0 y el siguiente paso de PWM
  escribe el pin: peor caso ≤ T_samp + T_ctrl + C_ctrl + T_samp + C_samp
  = `__` µs > 5 ms. Medido: `__` ms (máx. de 5 disparos).

**Decisión.**
1. En `cmd_calib`, `k_busy_wait(400)` → `k_usleep(400)`: la consola espera dormida
   en vez de girar.
2. En `task_sampling`, la rama que pone `estop` también pone `duty_pct = 0`, y el
   paso de PWM del mismo job baja la válvula.

**Números antes / después.**

| | Antes | Después |
|---|---|---|
| `calib` CPU | `__` ms | `__` ms (traza: `__` µs por settle × 1000) |
| `calib` duración | `__` ms | `__` ms |
| ¿Cabe en 1 s con Daniela? | no (`__` ms disponibles < `__` ms) | sí (`__` ms ≤ `__` ms) |
| E-stop detección → válvula baja (máx. de 5) | `__` ms | `__` µs |
| Suma peor caso del camino | `__` µs | T_samp + C_samp = `__` µs ≤ 5 ms |

Cada `k_usleep(400)` se redondea al tick (100 µs): 4 ticks + el tick en curso
≈ 0.5 ms, así que 1000 settles duran ≈ 0.5 s y sí caben en 1 s. Con un tick de 1 kHz
cada sleep duraría ≈ 2 ms (1 tick + el tick en curso) y `calib` tardaría ≈ 2 s:
volvería a incumplir el segundo, aunque casi sin usar CPU.

**Estado.** Aceptado e implementado.

## §3 — Evidencia semana 6

### Task A — Fig. 4.13 en vivo (REQ: ninguno del nodo; verificación de teoría)
- `A1_RM_miss.png`: RM, ventana de un hiperperiodo (35 ms). τ1 (DIO0/GPIO4), τ2 (DIO1/GPIO5),
  pérdida (DIO2/GPIO6), inicio de hiperperiodo (DIO3/GPIO7). Anotar: t = 5 ms τ1 desaloja
  a τ2; τ2 termina en t ≈ `__` ms > 7 ms; pulso de pérdida.
- `A2_EDF_ok.png`: EDF, mismo encuadre: en t = 5 ms τ2 sigue (deadline 7 < 10).
- `A3_EDF_sin_trigger.png`: trigger en el pin de pérdida, modo Normal, 60 s sin disparo.
- Consola: `A_RM_consola.txt`, `A_EDF_consola.txt` (línea de t = 60 s).
- Lectura: U = 0.971 > 0.828 (LL, n = 2): RM sin garantía y la RTA da R2 = 8 > 7: τ2
  pierde. EDF es exacto para U ≤ 1: no pierde.

### Task B — Inversión y su arreglo (REQ-CTRL-01)
- `B1_sin_contencion.png`, `B2_inversion_ksem.png`, `B3_mutex_PI.png`, anotadas segmento
  a segmento (quién corre: consola / control / telemetría / sampling).
- Consola: líneas `inv [lock=k_sem]` y `inv [lock=k_mutex]` (`B_consola.txt`).

### Task C — ADR-005 (REQ-ESTOP-01, REQ-CONS-01)
- `C1_estop_antes_1..5.png`, `C2_estop_despues_1..5.png`, `C3_calib_antes.png`,
  `C4_calib_despues.png`, `calib_cpu_traza.txt`, `C_consola.txt`.

## §4 — Planificabilidad

`analysis/rta.py` (en el repo), alimentado con los C_i medidos y B de Task B.
Salida completa: `rta_salida.txt`.

| Conjunto | U | LL (n(2^{1/n}−1)) | Hiperbólica (∏(U_i+1)) | RTA | Veredicto |
|---|---|---|---|---|---|
| Nodo actual | `__` | `__` → `__` | `__` → `__` | todos R ≤ D | |
| Nodo + 2 sensores de Daniela | `__` | `__` → `__` | `__` → `__` | `__` | `__` |

- RTA de control: sin bloqueo R = `__` µs (medido `__` µs); con B = `__` µs, R = `__` µs
  (medido con `k_mutex` `__` µs). La RTA acota ambas filas.
- ¿Por qué una captura de 30 s queda por debajo? La RTA supone el instante crítico
  (todas las tareas de mayor prioridad liberadas a la vez con su peor C); 30 s rara vez
  lo contienen. Si una captura superara la RTA, los C_i estarían mal medidos.
- `calib` y e-stop antes/después: ver ADR-005.
