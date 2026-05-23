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
