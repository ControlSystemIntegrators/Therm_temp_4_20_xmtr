# Analog 4–20 mA Thermistor Temperature Transmitter

A fully **analog** (no microcontroller) 2-wire 4–20 mA temperature transmitter
built from **standard, multi-sourced parts** — and a worked tutorial in the
instrumentation theory behind it.

It does two jobs:

1. **A teaching reference.** If you've ever wanted to understand how a 4–20 mA
   transmitter actually works — loop power, sensor excitation, linearization,
   zero/span calibration — this is a complete, honest, end-to-end example with
   the math shown and a calculator you can run.
2. **A real instrument.** It was designed for **chocolate temperature control**
   (the 20–40 °C tempering/working range), as a more accurate and more robust
   replacement for thermocouples. But it is parameterized: point the included
   calculator at *your* thermistor and *your* temperature band and it tells you
   which resistors to fit.

> **Why analog?** You can absolutely bolt a microcontroller and a 12-bit ADC on
> top of this for fine digital adjustment — see [Optional digital
> upgrade](#optional-digital-upgrade). In practice, for "hold a setpoint in a
> known band" process control, that layer is rarely worth the complexity. This
> project deliberately stays in the analog domain so the whole signal path is
> visible and every part is replaceable.

> **Not a safety device.** This is a process measurement instrument, not a
> safety-rated (SIL) one. Don't use it as a protective function.

---

## Specifications (default build)

| Parameter | Value |
|---|---|
| Output | 4–20 mA, 2-wire loop-powered |
| Loop supply | 7–30 V (24 V typical) |
| Default range | **20–40 °C → 4–20 mA** (chocolate) |
| Sensor | NTC thermistor, 10 kΩ @ 25 °C, β ≈ 3892 K (e.g. Omega 44006) |
| In-band conformity | **±0.06 °C** (electronics + linearization; sensor adds its own interchangeability tolerance) |
| Calibration | zero + span trimpots, non-interactive |
| Quiescent current | ~1.5–2 mA (fits under the 4 mA floor) |
| Components | jellybean / multi-sourced; op-amps in SOT-23-5 |

Outside the chosen band the output saturates near 4 mA (cold) or 20 mA (hot) —
intentional. Accuracy is only specified inside the band.

---

## How a 4–20 mA transmitter works (the theory)

**The current loop.** A 2-wire transmitter sits in series with a DC supply and
a receiver. The transmitter's job is to *draw a controlled current* from the
loop — 4 mA represents the bottom of the range, 20 mA the top — regardless of
loop voltage or wiring resistance (within limits). Because the *current* is the
signal, voltage drops in long cable runs don't corrupt the reading, and a broken
wire reads 0 mA (a detectable fault, distinct from a valid 4 mA "low"). That
noise immunity and fault detection is why 4–20 mA has survived for decades in
industry.

**Loop-powered ("2-wire").** The same two wires that carry the signal also power
the transmitter. The catch: the *entire* circuit must run on **less than 4 mA**,
because that floor is the lowest the loop ever provides. Every microamp the
electronics draw is part of the loop current, so the design budgets quiescent
current carefully and lets an output ("dump") transistor make up the difference
to hit the commanded 4–20 mA.

**Why a thermistor?** An NTC thermistor is cheap, has a large signal (thousands
of ohms change over our band), is available with tight interchangeability
(±0.1–0.2 °C for the Omega 44000 series), and needs no cold-junction
compensation like a thermocouple. Its one drawback is that it is **very
nonlinear** — which is the interesting part of this design.

---

## The nonlinearity problem (and the one-resistor fix)

An NTC's resistance is approximately

```
R(T) = R25 · exp( β · (1/T − 1/298.15) )      [T in kelvin]
```

For our 10 kΩ part that's ~57 kΩ at −10 °C falling to ~3.6 kΩ at +50 °C — about
15:1, and badly curved. Fed straight into a linear amplifier you'd get large
errors away from one calibration point.

**The fix is a single resistor in parallel with the thermistor.** The parallel
combination `Rt ∥ Rlin` has an S-shaped curve with an inflection point; placing
that inflection at the *center* of your band makes the network resistance very
nearly linear in temperature there. The value for maximum linearity at center
temperature `Tc` (kelvin) is:

```
Rlin = Rt(Tc) · (β − 2·Tc) / (β + 2·Tc)
```

For the chocolate build (center 30 °C) that's **5.90 kΩ**, and the residual
nonlinearity across 20–40 °C is only **±0.06 °C**.

### Why one resistor and not two

A second resistor *can* add a curvature-shaping term (by exciting through a
divider instead of a constant current), so we checked whether it's worth it.
For an NTC it essentially isn't — the optimizer drives the second resistor back
toward "constant current," and the conformity barely moves:

| Band → 4–20 mA | 1 resistor | 2 resistors |
|---|---|---|
| 20–40 °C | ±0.061 °C | ±0.057 °C |
| 15–45 °C | ±0.207 °C | ±0.188 °C |
| −10–50 °C | ±1.585 °C | ±1.545 °C |

~5% improvement for an extra precision part and an extra calibration
interaction. We dropped it. **The real lever is band width, not resistor count**
(see the table — the wider the band, the worse the conformity). Pick the
narrowest band that covers where your process actually operates.

You can reproduce all of this — and design for your own sensor/range — with
[`tools/design.py`](tools/design.py).

---

## Circuit overview

Two views: the **signal chain** (what computes the current) and the
**power/output loop** (how a 2-wire device powers itself and sets loop current).

### Signal chain

```
 Vref(2.5V) ──[ NTC ∥ Rlin ]──● X ─────────────►┌────────────┐
                              │                 │   A2       │
              A1 sinks Iexc ──┘                 │ gain/zero  │─ Vcmd ─►┌──────────┐
              (0.25 mA, constant)               │  (2 pots)  │         │ A3 servo │─► loop
                                                └────────────┘         │  + Q2    │   current
   V(X) = Vref − Iexc·(NTC ∥ Rlin)                                     └──────────┘
        (rises with temperature)        Vcmd = SPAN·(V(X) − ZERO)   Iloop = Vcmd / Rsense
```

A constant current is pulled through the linearized network, so the node voltage
`V(X)` is a clean, near-linear function of temperature. The gain/zero amplifier
scales and offsets it; the output stage turns that command voltage into loop
current.

### Power / output loop

```
 LOOP+ ──▷|──┬───────────────────────────────┬──────────► IN (raw 7..30 V)
   (24 V) D1 │                               │
           TVS         pre-reg: Q1 + TLV431 ──┤────────► VL (+5 V) ─► Vref, A1, A2, A3
            │          (series NPN follower)  │
            │                                 └────────► Q2 collector (dump)
            │                                                  │ emitter
 LOOP- ─────┴────────────────[ Rsense 50Ω ]──────  AGND ───────┘
                                    ▲
                A3 drives Q2 so that  Iloop · Rsense = Vcmd
```

Everything returns to `AGND` and flows out through `Rsense`, so the
sense resistor sees the **total** loop current — the electronics' own ~1.7 mA
quiescent draw plus whatever the dump transistor `Q2` adds. A3 servos `Q2` until
that total equals `Vcmd / Rsense`. Because quiescent draw (~1.7 mA) is below the
4 mA floor, `Q2` always has something to add.

### Stage-by-stage

| Stage | Parts | Function | Key relation |
|---|---|---|---|
| Protection | D1 (Schottky), TVS | reverse-polarity + surge | — |
| Pre-regulator | Q1 (NPN follower), TLV431, divider | makes the +5 V rail `VL` from the loop; **series** pass, not shunt, so it draws only what the electronics need | `VL = 1.24·(1+Rfa/Rfb)` |
| Reference | LM4040-2.5 | 2.500 V for excitation + zero | — |
| Excitation | A1, Q3, Rexc | constant `Iexc = Vref/Rexc = 0.25 mA` pulled through `NTC∥Rlin` | `V(X)=Vref − Iexc·Rnet` |
| Linearization | Rlin (5.90 kΩ) | straighten the curve in-band | `Rlin = Rt(Tc)·(β−2Tc)/(β+2Tc)` |
| Gain/Zero | A2 + **span pot** + **zero pot** | scale & offset to the command voltage | `Vcmd = SPAN·(V(X) − ZERO)` |
| Output | A3, Q2, Rsense | servo loop current to the command | `Iloop = Vcmd / Rsense` |

> **The three knobs are orthogonal**, which makes calibration sane:
> **Rlin** depends only on the band *center*, **span** on the band *width*, and
> **zero** on the band *position*. Move the band up/down → re-zero only. Widen
> it → re-span only. Re-center it → change Rlin.

---

## Selecting components for your own range

Run the calculator with your sensor and the two temperatures you want at 4 mA
and 20 mA:

```
python3 tools/design.py --r25 10000 --beta 3892 --tlow 20 --thigh 40
```

It prints the linearization resistor, the excitation resistor, the span (gain)
and zero (offset) targets, the conformity error you'll get, the self-heating
estimate, and a transfer table. Defaults are the chocolate build. Output for the
default:

```
--- Linearization ---
Rlin (E96)      : 5.900 kohm   <- parallel with thermistor
Conformity      : +/- 0.059 C
--- Excitation ---
Rexc (E96)      : 10.000 kohm  -> Iexc = 0.2500 mA
--- Amplifier / output stage ---
SPAN  (gain)    : 2.6635 V/V   <- set by span pot
ZERO  (Vzero)   : 1.4230 V     <- set by zero pot
```

**Manual recipe** (what the script does):

1. **Center → Rlin.** `Tc = (Tlow+Thigh)/2`; `Rlin = Rt(Tc)·(β−2Tc)/(β+2Tc)`,
   rounded to the nearest E96 value.
2. **Excitation.** Pick `Iexc` (~0.25 mA is a good balance of signal size vs.
   self-heating); set `Rexc = Vref / Iexc`.
3. **Edge voltages.** `V(X) = Vref − Iexc·(Rt ∥ Rlin)` at `Tlow` and `Thigh`.
4. **Span (gain).** `SPAN = (20mA−4mA)·Rsense / (V(X)@Thigh − V(X)@Tlow)`.
5. **Zero (offset).** Choose `ZERO` so the output is 4 mA at `Tlow`.

Then check the printed conformity. If it exceeds your target, your band is too
wide — narrow it (see the table above).

---

## Calibration

You need a way to present two known temperatures (a stirred ice/water-and-warm
bath, a dry-block calibrator, or — easiest for bench bring-up — **two precision
resistors** substituted for the probe equal to `Rt(Tlow)` and `Rt(Thigh)`, which
the calculator prints).

1. Apply the **low** point (`Tlow`, e.g. 20 °C → `Rt = 12.49 kΩ`). Adjust the
   **ZERO** pot for **4.00 mA**.
2. Apply the **high** point (`Thigh`, e.g. 40 °C → `Rt = 5.35 kΩ`). Adjust the
   **SPAN** pot for **20.00 mA**.
3. Repeat once. Zero and span interact only slightly (the gain term scales the
   zero point a little), so a second pass nails both to within a microamp.

Use a loop calibrator or a 250 Ω precision resistor + DMM (1.000–5.000 V = 4–20
mA) to read the current.

---

## Bill of materials (multi-sourced)

Every active part below is available from multiple manufacturers, or in a
footprint with many drop-in alternatives. That is a design goal: this instrument
should be repairable for decades without a single-source IC.

| Ref | Part | Function | Second-source notes |
|---|---|---|---|
| RT1 | NTC 10 kΩ, β≈3892 (Omega 44006 / equiv.) | sensor | any 10k NTC with known β; re-run calculator for other betas |
| Rlin | 5.90 kΩ, 0.1%, ≤25 ppm/°C | linearization | passive, universal |
| U1 | LM4040-2.5 (2.500 V) | reference | TI, ADI, Diodes, ON |
| U2 | TLV431 (or TL431) | pre-reg reference | TI, ON, Diodes, ST, UTC |
| Q1 | NPN small-signal (MMBT3904 / BC847) | pre-reg pass (follower) | universal |
| Q2 | NPN, ~0.5 W (SOT-223, e.g. BCP56 / PZTA42) | output dump transistor | universal; **see thermal note** |
| Q3 | NPN small-signal (MMBT3904 / BC847) | excitation current sink | universal |
| A1–A3 | µpower precision op-amp, **SOT-23-5** (OPA333 / MCP6V31 / TLV9061-class) | excitation, gain/zero, output servo | by exact PN limited; by SOT-23-5 footprint, dozens of swappable parts |
| Rexc | 10.0 kΩ, 0.1% | sets Iexc | passive |
| Rsense | 49.9 Ω (or 50 Ω), 0.1%, ≤25 ppm/°C | loop sense | passive |
| Rfa/Rfb | 30.1 kΩ / 10.0 kΩ, 1% | sets VL = 5 V | passive |
| RV1 | zero trim, multiturn cermet (e.g. 3296W) | ZERO | universal |
| RV2 | span trim, multiturn cermet | SPAN | universal |
| D1 | Schottky (BAT54 / 1N5819) | reverse polarity | universal |
| TVS1 | SMAJ33A (or per supply) | surge | universal |
| C1–Cn | 100 nF + 1–10 µF bypass | decoupling | universal |

**Thermal note (Q2).** A 2-wire transmitter must drop the loop voltage somewhere;
that's Q2. Worst case ≈ (instrument voltage) × (loop current) ≈ 20 V × 20 mA ≈
**0.4 W**. Use a SOT-223 (or larger) device with adequate copper, or split the
drop with a series resistor ahead of Q2's collector.

**Op-amp footprint.** Standardizing A1–A3 on **SOT-23-5 singles** is deliberate:
precision op-amps are mostly single-source by part number, but the SOT-23-5
single-op-amp pinout is a de-facto industry standard with many footprint-
compatible options, so a substitute is always a re-qualification away, never a
redesign.

---

## Simulation

[`sim/transmitter.cir`](sim/transmitter.cir) models the ideal signal chain
(reference + op-amps as behavioral sources, NTC as a temperature-dependent
resistor) and DC-sweeps temperature to confirm the 4–20 mA transfer and in-band
linearity.

```
ngspice -b sim/transmitter.cir   # DC-sweeps temperature; prints Iloop vs T
```

(LTspice: change the behavioral-resistor `r='...'` syntax to `R=...`.)

It has been run with **ngspice 46**; the full output is saved in
[`sim/SIM_RESULTS.txt`](sim/SIM_RESULTS.txt). Key points (Iloop = Vcmd / 50 Ω):

| T (°C) | V(x) | Vcmd | Iloop |
|---|---|---|---|
| 20 | 1.49812 V | 0.20009 V | **4.00 mA** |
| 30 | 1.64825 V | 0.59996 V | **12.00 mA** |
| 40 | 1.79854 V | 1.00024 V | **20.00 mA** |
| <20 | — | clamps 0.190 V | 3.8 mA (under-range) |
| >40 | — | clamps 1.025 V | 20.5 mA (over-range) |

The node voltages match `tools/design.py` to the millivolt, and the in-/out-of-
band clamping behaves as designed.

**Verification status (be honest about it):**

- ✅ Signal-chain transfer and **±0.06 °C in-band conformity** — verified in
  `tools/design.py` **and confirmed in ngspice** (table above).
- ⬜ Discrete output stage (the Q1 pre-regulator and the Q2/A3 servo loop,
  including loop stability and Q2 thermals) — **designed but not yet
  device-level simulated or bench-verified.** The netlist above models the
  op-amps as ideal behavioral sources, so it validates the *transfer math*, not
  the real parts. Simulate with device models and prototype before trusting it.

---

## Optional digital upgrade

If you later want digital trim, datalogging, or a nonlinear curve over a wide
range, you can add an MCU with a ≥12-bit ADC reading `V(X)` and driving the loop
via a current-output DAC (or by replacing the A3/Q2 stage). For a "hold a
setpoint in a known band" application this is usually unnecessary complexity —
the analog path here already beats thermocouple accuracy in-band — but the
sensor front-end and linearization theory carry over unchanged.

---

## Repository layout

```
analog-temp-transmitter/
├── README.md              # this file
├── tools/
│   └── design.py          # parameterized design calculator (no dependencies)
└── sim/
    └── transmitter.cir    # ngspice/LTspice transfer-function verification
```

Planned next: a KiCad schematic + PCB, and a device-level SPICE model of the
output stage.

## License

Intended for public release — choose a license before publishing (MIT for the
code/docs, CERN-OHL-S or similar for hardware are common choices). No license
file is committed yet.
