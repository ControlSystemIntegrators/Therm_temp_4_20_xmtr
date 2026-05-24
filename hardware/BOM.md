# Bill of Materials

Design-candidate BOM for the analog 2-wire 4–20 mA NTC transmitter
(default build: 20–40 °C → 4–20 mA, chocolate temperature control).

> **Status:** the *functional* parts list is complete and orderable. A handful
> of bias/compensation values (marked **nominal**) may shift slightly once we
> finalize the interconnections and run the device-level simulation — they don't
> affect what you buy, only trim values. Machine-readable copy: [`BOM.csv`](BOM.csv).

Every active part is multi-sourced or in a footprint with many drop-in
alternatives — maintainability is the design goal.

---

## Reference designators by stage

### Sensor & linearization
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| RT1 | NTC 10 kΩ @ 25 °C, β≈3892 | ±0.1–0.2 °C interch. | Thermistor probe (Omega 44006 / ON-960-44xxx), wired to TB1 |
| R1 | 6.04 kΩ | 1%, ≤25 ppm/°C | **Linearization** resistor, parallel with RT1 (tempco-critical; re-optimized for gain-stage loading) |

### Voltage reference
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| U1 | LM4040-2.5 (2.500 V) | A/B grade | Shunt voltage reference |
| R2 | 2.49 kΩ | 1% | U1 bias from VL (≈1.0 mA, keeps LM4040 above its load) |
| C7 | 100 nF | X7R | VREF_U1 reference bypass |

### Pre-regulator (makes the +5 V rail VL from the loop)
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| Q1 | MMBT3904 (NPN) | — | Series-pass emitter follower |
| U2 | TL431 (any second-source; KiCad sym `TL431DBZ`, SOT-23) | — | Adjustable shunt reference, 2.5 V (sets VL) |
| Q4 | MMBT3906 (PNP) | — | Bias current source — high-side pass device (feeds U2 cathode + Q1 base) |
| Q5 | MMBT3906 (PNP) | — | Bias current source — current-sense device (limits Q4) |
| R17 | 432 Ω | 1% | Sets bias current `I ≈ 0.65 V / R17 ≈ 1.5 mA` (Q4 emitter) |
| R18 | 100 kΩ | 1% | Q4 base pull-down (turn-on), returned to AGND |
| R3 | 10.0 kΩ | 1% | VL feedback divider, top |
| R4 | 10.0 kΩ | 1% | VL feedback divider, bottom → VL ≈ 2.5·(1+R3/R4) = 5.00 V |
| R5 | 100 kΩ | 1% | Q1 base–emitter (clean turn-off) — *nominal* |
| C2 | 1 µF | X7R 50 V | VL bulk decoupling |

### Excitation (constant-current sink, 0.25 mA through RT1‖R1)
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| A1 | OPA333 (SOT-23-5) | — | Current-sink servo amp |
| Q3 | MMBT3904 (NPN) | — | Current-sink pass device |
| R6 | 10.0 kΩ | 1% (matched) | Setpoint divider top (Vref → Vsp ≈ 0.5 V) |
| R7 | 2.49 kΩ | 1% (matched) | Setpoint divider bottom |
| R8 | 2.00 kΩ | 1%, ≤25 ppm/°C | Sink emitter resistor → **sets Iexc = Vsp/R8 ≈ 0.25 mA** (tempco-critical) |
| C3 | 100 pF | C0G | A1 loop compensation — *nominal* |

### Gain / Zero amplifier (difference amp + calibration pots)
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| A2 | OPA333 (SOT-23-5) | — | Gain/zero (span) amplifier |
| R9 | 100 kΩ | 1% (matched) | Diff-amp input (V(X)) — high-Z to avoid loading node X |
| R10 | 100 kΩ | 1% (matched) | Diff-amp input (Vzero) |
| R11 | 249 kΩ | 1% (matched) | Diff-amp feedback (fixed part of SPAN) |
| R12 | 249 kΩ | 1% (matched) | Diff-amp CMRR-match resistor (= R11; small gain mismatch is calibrated out) |
| RV1 | 50 kΩ cermet, multiturn, **SMD** (Bourns 3269 / 3224) | — | **SPAN** trim (in series with R11 → gain 2.49–2.99) |
| R13 | 100 kΩ | 1% | Zero network, top (Vref side) → Vzero range 1.0–1.5 V (sized for the 50 kΩ pot) |
| R14 | 100 kΩ | 1% | Zero network, bottom (AGND side) |
| RV2 | 50 kΩ cermet, multiturn, **SMD** (Bourns 3269 / 3224) | — | **ZERO** trim (wiper = Vzero ≈ 1.0–1.5 V) |
| C4 | 1 nF | C0G | Feedback noise filter (~6 kHz) — *nominal* |
| C5 | 100 nF | X7R | Zero-node bypass |

### Output stage (2-wire current servo)
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| A3 | OPA333 (SOT-23-5) | — | Loop-current servo amp |
| Q2 | BCP56-16 (NPN, SOT-223) | ≥1 W, ≥80 V | **Dump transistor** — drops the loop voltage; see thermal note |
| R16 | 49.9 Ω | 1%, ≤25 ppm/°C | Loop current sense (Iloop = Vcmd / R16) (tempco-critical) |
| R15 | 2.49 kΩ | 1% | Q2 base drive — *nominal* |
| C6 | 10 nF | X7R | Output servo-loop compensation — *nominal* |

### Protection & I/O
| Ref | Value | Tol/Grade | Description |
|---|---|---|---|
| D1 | SS14 (SMA) | Schottky, ≥40 V | Reverse-polarity protection (series in LOOP+) |
| TVS1 | SMAJ33A | uni-dir | Surge clamp across loop |
| C8 | 1 µF | X7R 50 V | Input bulk (IN ↔ AGND) |
| C9 | 100 nF | X7R 50 V | Input bypass (IN ↔ AGND) |
| C1, C10, C11 | 100 nF ×3 | X7R | Op-amp decoupling — one per A1/A2/A3 (at pin 5 ↔ AGND) |
| TB1 | 2-pos terminal block, 5.08 mm | — | Thermistor probe leads |
| TB2 | 2-pos terminal block, 5.08 mm | — | 4–20 mA loop (LOOP+ / LOOP−) |

---

## Op-amp choice (A1–A3)

**OPA333** (SOT-23-5) is the reference part: 17 µA supply current each (51 µA
total — easily inside the loop budget), 10 µV offset, 0.05 µV/°C drift, 5.5 V max
supply. Standardizing on the **SOT-23-5 single-op-amp footprint** means many
pin-compatible alternatives (ADA4505-1, MCP6V11, TLV9061, LPV811-class) can drop
in — single-source by exact PN, multi-source by footprint.

## Thermal note (Q2)

A 2-wire transmitter must drop the loop voltage somewhere — that's Q2. Worst case
≈ (instrument voltage) × (loop current) ≈ 25 V × 20 mA ≈ **0.5 W**. The SOT-223
BCP56 handles it with adequate copper pour; if your loop supply is high, add a
small series resistor ahead of Q2's collector to share the dissipation.

## Current budget (why it fits 2-wire)

| Consumer | Current |
|---|---|
| 3 × OPA333 | ~0.05 mA |
| VREF_U1 path via R2 (LM4040 bias + 0.25 mA excitation + zero/setpoint dividers) | ~1.0 mA |
| Pre-reg bias (Q4/Q5 source) | ~1.5 mA |
| **Total quiescent** | **~2.6 mA** |

Under the 4 mA floor with ~1.4 mA of margin; the dump transistor Q2 supplies the
difference up to 20 mA.

> **Why the bias source is 1.5 mA, and why it's two transistors.** U2 is a
> standard **TL431**, which needs ~1 mA minimum cathode current to regulate. The
> bias source feeds U2's cathode plus Q1's base (~8 µA), so it's sized to ~1.5 mA
> to keep U2 in regulation with margin. It must be a *constant* current (not a
> resistor) because the voltage across it swings ~1.3–24 V over the 7–30 V loop —
> a resistor would vary the current ~18:1 and blow the budget at high loop
> voltage. We build that constant current from **Q4/Q5 (MMBT3906 ×2) + R17/R18**
> rather than a current-regulating diode: a CRD is a specialty part with only a
> handful of second-sources, whereas this discrete source is all jellybean. Q5
> senses Q4's emitter current across R17 and throttles Q4 when `I·R17 ≈ 0.65 V`,
> giving `I ≈ 0.65 V / R17`. R18's own current returns to AGND (not the bias
> node) and stays a negligible ~15–80 µA across the loop range.
>
> The earlier TLV431 (1.24 V, ~0.1 mA min) allowed a 0.5 mA bias, but it isn't in
> KiCad's stock library and is less widely second-sourced. We took the +1 mA
> quiescent to land on the most-multi-sourced reference in existence with a stock
> symbol + footprint. If the budget is ever tight, the **ATL431** (2.5 V, ~35 µA
> min, same divider) buys it back — at the cost of fewer sources and a custom
> symbol.

---

## Tolerance & tempco

The two trimpots calibrate the instrument at two points (4 mA at Tlow, 20 mA at
Thigh), so **any pure gain or offset error is trimmed out**. That splits the
resistor spec into two very different requirements — *initial tolerance* (mostly
calibrated away) and *tempco* (drift after calibration, **not** calibrated away).

**Initial tolerance — 1% is fine almost everywhere.**
A gain/offset error just moves a trimpot. The only resistor whose tolerance
escapes calibration is **R1 (linearization)**, because it sets the *shape* of the
curve between the two anchored endpoints — and even there it's nearly free: a
1% R1 error widens conformity from ±0.060 °C to ±0.067 °C (±5% → ±0.10 °C). So
spec **1% tolerance on all of R1, R6–R12, R16**; the precision used to be 0.1%
but it bought essentially nothing here.

**Tempco — this is what actually matters, and only on three resistors.**
Drift happens after calibration, so it isn't trimmed. It bites hardest on the
**single-ended (non-ratio) resistors**, where there's no matching partner to
cancel against:

- **R16** (loop sense, `Iloop = Vcmd/R16`) — drifts output gain 1:1.
- **R8** (excitation set, fixes Iexc) — drifts the signal slope.
- **R1** (linearization) — drift slightly reshapes the network.

At 100 ppm/°C (typical 1% thick-film) these add roughly **0.04–0.05 °C each over a
20 °C ambient swing**; at ≤25 ppm/°C they're ~4× smaller. So keep **R1, R8, R16
at ≤25 ppm/°C** (1%-tolerance / 25-ppm thin-films are cheap) — that keeps the
ambient drift comfortably inside the ±0.1 °C system spec. At 100 ppm/°C the
stacked drift of these three can eat much of that budget over a wide ambient
range, on top of the sensor's own ±0.1–0.2 °C interchangeability.

**Ratio groups — 1%/100 ppm OK if bought matched.**
R6/R7 (excitation divider) and R9/R10/R11/R12 (diff-amp) work as *ratios*, so if
they're the same series/material their tempcos track and largely cancel. 1% is
fine; a matched resistor network for the diff-amp set is ideal but not required.

| Class | Refs | Spec |
|---|---|---|
| Single-ended, drift-critical | **R1, R8, R16** | 1%, **≤25 ppm/°C** |
| Ratio / matched | R6, R7, R9, R10, R11, R12 | 1% (same series) |
| Bias / divider / non-critical | R2, R3, R4, R5, R13, R14, R15, R17, R18 | 1% |
| Caps | C3, C4 timing/filter | **C0G**; all bypass/bulk **X7R** |

## Packaging

The board is **all surface-mount** — every active part is SOT-23 / SOT-23-5 /
SOT-223, and all R/C, the trimpots (SMD multiturn), D1 (SS14, SMA) and TVS1
(SMA) are SMD. The **only through-hole parts are TB1/TB2**, the field-wiring
terminal blocks — a deliberate exception, because TH gives the pull-out strength
an SMD terminal block can't for a probe/loop cable that gets tugged in service.
