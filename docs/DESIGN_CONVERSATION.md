# How this was designed — the driving prompts

This project was designed interactively, in conversation with an AI assistant
(Claude / Claude Code). It's published here partly *because* the back-and-forth
is itself a decent walkthrough of how you reason about an analog instrument:
each prompt below narrowed the design space, and the decision it produced is
noted underneath.

Prompts are the human's, reproduced in order. (The structured multiple-choice
answers were posed by the assistant; the human's selection is shown.)

---

**1.** *"hey are you any good at analog circuits?"*

> Opening. Established scope.

**2.** *"I am interested in making an analog 4-20ma temperature transmitter for
tempature measurement in the range of -10-50degC. Accuracy is only really
critical in a small range of temperatures, 20-40degc. I would like to use a
thermistor as the measurement source. I am thinking probes such as these
[Omega ON-960-44000 non-linear thermistor probe]."*

> The core spec: −10…50 °C range, tight accuracy only in 20–40 °C, NTC
> thermistor (10 kΩ @ 25 °C, β ≈ 3892). The "accuracy only matters in a band"
> constraint became the central lever of the whole design.

**3.** Assistant asked: power architecture? accuracy? build style?
Human: **3-wire/4-wire**, **±0.1–0.2 °C**, and asked
*"what's the cost difference in parts between the purpose built ic architecture
and the fully discrete solution?"*

> Answer: roughly a wash (~$16 vs ~$18 in single quantities) — the integrated
> loop IC (XTR116) bundles the reference + output stage that you'd otherwise buy
> discretely.

**4.** *"are there pin compatible semiconductors from other manufacturers for
the xtr106?"*

> Answer: no — the entire XTR1xx family (and every integrated 4–20 mA loop
> transmitter IC) is single-source.

**5.** *"ok, let's consider it a 2-wire instrument. The reason that I want pin
compatibility from multiple manufacturers is because I want to make sure that
the product is always maintainable."*

> The decisive constraint. Because no integrated loop IC is multi-sourced,
> maintainability forces a **fully discrete design from jellybean parts**. This
> set the whole BOM philosophy.

**6.** Assistant proposed band-anchoring + a parallel linearization resistor.
Human: *"those resistors for linearization — one adjusts the zero? and one the
span? and they are non-interactive? I think band anchored is probably OK. I
would want instructions for selecting the components to anchor the band around
particular values…"*

> Clarified the orthogonal-knobs model: linearization (curve), zero (position),
> span (width) are separate. Drove the requirement for a **parameterized
> component-selection recipe** (now `tools/design.py` + the README).

**7.** *"I think that standardizing around SOT23-5 is the way to go."*

> Op-amps fixed to the SOT-23-5 footprint — a de-facto multi-vendor standard,
> serving the maintainability goal.

**8.** *"I am ok with a dual linearization resistor approach, in that case, and
I would hope for a zero and span potentiometer for calibration."*

> Triggered a numerical comparison of one- vs two-resistor linearization. The
> result: the second resistor buys only ~5% for an NTC, so it was **dropped**.
> Zero + span trimpots stayed.

**9.** Assistant asked which band → 4–20 mA. Human: *"20–40 deg C is fine. I
would prefer a readme that describes how to select components to meet particular
ranges… my application, which is chocolate temperature control. Right now, we
are using thermocouples, which are not very accurate, and the temperatures that
we care about are 20–40C. … a microprocessor can be added to this using a 12-bit
adc … but practically speaking, that adds a very complicated layer … which …
is pretty much never needed."*

> Locked the default range (20–40 °C), the real application (chocolate, replacing
> thermocouples), the dual mission (working instrument **and** teaching repo),
> and the "stay analog" stance.

**10.** *"we can do an ngspice analysis. also a git init. Roll this out as
'Therm_temp_4_20_xmtr' repo."*

> Verification + packaging. (ngspice 46 was installed portable; the netlist
> confirms 4.00/12.00/20.00 mA at 20/30/40 °C — see `sim/SIM_RESULTS.txt`.)

**11.** *"please proceed, but with email as bruce@controlsysint.com"* —
git identity.

**12.** *"we can use the controlsysint remote…"* — published to the
ControlSystemIntegrators GitHub account.

**13.** *"also, MIT license is fine for this."* — see `LICENSE`.

**14.** *"feel free as well to include a transcript of the prompts that drove
this effort."* — this file.

---

### The throughline

A single constraint — *"accuracy only matters in 20–40 °C"* — combined with
*"it must always be maintainable"* drove every major choice: band-anchored
calibration, a single parallel linearization resistor, a discrete signal chain
of multi-sourced parts, SOT-23-5 op-amps, and a parameterized calculator so the
same design retargets to any sensor and band.

---

## Round 2 — design review, jellybean/SMD pass, and device-level verification

A second pass took the design from "math validated" to "schematic + PCB," and
in doing so caught several real issues. The driving prompts, in order:

**15.** *"a part more common than TLV431… is there a more common adjustable
shunt regulator?"*

> Swapped the pre-regulator reference **TLV431 → plain TL431** (the most
> second-sourced shunt regulator in existence, and in KiCad's stock library as
> `TL431DBZ`, 3-lead SOT-23 — the TLV431 was a custom symbol). Divider became
> R3=R4=10 k for `VL = 2.5·(1+R3/R4) = 5 V`. Cost: ~+1 mA bias (TL431 needs
> ~1 mA min cathode current) — accepted for ubiquity + a stock symbol.

**16.** *"glad to make a completely jellybean design."*

> The current-regulating diode biasing the reference was the only specialty
> semiconductor left. Replaced it with a **2-transistor constant-current source**
> (Q4/Q5 = MMBT3906 ×2 + R17/R18) — all jellybean, ~1.5 mA, flat over the
> 7–30 V loop.

**17.** *"I would like everything to be surface mount."*

> Trimpots → SMD multiturn (Bourns 3269/3224), D1 → SS14 (SMA). The **only**
> through-hole parts left are the field-wiring terminal blocks — a deliberate
> exception for pull-out strength.

**18.** *"reframe it to ±0.1 °C over 20 °C"* (after a tolerance/tempco review).

> Established that two-point calibration absorbs gain/offset error, so **initial
> tolerance can be 1 % everywhere**; only **tempco** matters, and only on the
> single-ended R1/R8/R16 (keep ≤25 ppm/°C). The headline spec was reframed from
> a false-precision ±0.06 °C to an honest **±0.1 °C over the band**, since sensor
> interchangeability and self-heating dominate anyway.

**19.** *"minimize the total number of different kinds of resistors."*

> Consolidated to **8 distinct resistor values** by re-spec'ing where the value
> is calibrated out (e.g. R2→2.49 k, R12→24.9 k, R13→10 k, R18→100 k).

**20.** *"a wire-by-wire of the … circuit"* → full netlist review.

> Walked the schematic net-by-net (via `kicad-cli` netlist export, not coordinate
> parsing). Caught and fixed: A1 powered from VREF instead of VL; the LM4040
> reference miswired across the loop input as if it were the TVS; D1 reversed; a
> fragmented IN rail with Q2's collector islanded; missing R2; and a 49.9 kΩ
> loop-sense typo (should be 49.9 Ω).

**21.** *"write the device-level netlist"* → discovered a spec-breaking flaw.

> A device-level SPICE model (real BJTs + behavioral OPA333/LM4040/TL431) showed
> the single-op-amp difference amp's input network (`R9+R12`) **loads the sensor
> node**, bowing V(x) to **±0.18 °C** — past spec. The ideal netlist and the
> first `design.py` both missed it (they assumed infinite input impedance). Fix:
> raise the diff-amp input impedance (`R9=R10=100 k`, `R11=R12=249 k`) **and**
> re-optimize R1 (→6.04 k). `design.py` now models the load (`--rload`); the
> device sim confirmed conformity back to **±0.058 °C**.

**22.** *"verify resistor and capacitor values"* + cap connectivity review.

> Reconciled every cap to its actual node (C1 = A1 decoupling, C7 = VREF bypass,
> etc.) and added input-rail decoupling (C8 bulk + C9 bypass, IN↔AGND).

**23.** *"I did a rough PCB layout. Push that and the schematic up."*

> Schematic + PCB committed alongside the updated BOM, README, calculator, and
> the device-level netlist.

### The Round-2 throughline

The math was right from Round 1, but **the physical circuit had bugs the ideal
model couldn't show** — a loaded sensor node, mis-wired references, a sense-
resistor typo. The lesson: a parameterized calculator proves the *intent*; a
net-by-net review and a *device-level* sim are what prove the *instrument*.
