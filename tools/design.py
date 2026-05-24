#!/usr/bin/env python3
"""
Design calculator for the analog 4-20 mA NTC thermistor transmitter.

Given a thermistor (R25, beta) and the temperature band you want to map to
4-20 mA, this prints the linearization resistor, the amplifier gain (span) and
offset (zero), the conformity (linearity) error you can expect inside the band,
and the loop-current current budget.

No third-party dependencies -- standard library only.

    python3 design.py                  # uses the CONFIG block below
    python3 design.py --tlow 15 --thigh 45 --r25 10000 --beta 3892

The math is documented in ../README.md ("How it works" and "Selecting
components for your own range").
"""

import argparse
import math

# --------------------------------------------------------------------------
# CONFIG -- defaults are the chocolate-tempering build (20-40 C -> 4-20 mA)
# --------------------------------------------------------------------------
DEFAULTS = dict(
    r25=10000.0,    # thermistor resistance at 25 C  (Omega 44006 = 10 k)
    beta=3892.0,    # thermistor beta (25/85 C)       (44006 ~ 3892 K)
    tlow=20.0,      # temperature that should read 4 mA  (deg C)
    thigh=40.0,     # temperature that should read 20 mA (deg C)
    iexc=0.25e-3,   # excitation current through the sensor network (A)
    vref=2.500,     # voltage reference (LM4040-2.5)  (V)
    rsense=50.0,    # loop current-sense resistor (ohm); Iloop = Vcmd / Rsense
    diss=5.0e-3,    # probe dissipation constant (W/degC) for self-heat estimate
    rload=349000.0, # gain-stage input resistance (R9+R12) loading node X to AGND.
                    # The single-op-amp difference amp hangs R9+R12 on the sensor
                    # node; this finite load bows V(x) and degrades conformity.
                    # Large => negligible. 34.9k = old (10k+24.9k); 349k = fixed.
)

# E96 1% / 0.1% mantissas (one decade)
E96 = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
    1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
    1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
    2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
    3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
    5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
    7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76,
]


def e96(value):
    """Nearest E96 standard resistor value."""
    if value <= 0:
        return value
    decade = math.floor(math.log10(value))
    best, err = value, float("inf")
    for d in (decade - 1, decade, decade + 1):
        for m in E96:
            cand = m * 10 ** d
            e = abs(cand - value) / value
            if e < err:
                best, err = cand, e
    return best


def rt(tc, r25, beta):
    """NTC resistance (ohm) at temperature tc (deg C), beta model."""
    t = tc + 273.15
    return r25 * math.exp(beta * (1.0 / t - 1.0 / 298.15))


def rnet(tc, r25, beta, rlin):
    """Thermistor in parallel with the linearization resistor."""
    r = rt(tc, r25, beta)
    return r * rlin / (r + rlin)


def rlin_for_center(tc, r25, beta):
    """Parallel resistor giving maximum linearity at center temp tc (deg C).
    Rlin = Rt(Tc) * (beta - 2*Tc_K) / (beta + 2*Tc_K)
    """
    tk = tc + 273.15
    return rt(tc, r25, beta) * (beta - 2 * tk) / (beta + 2 * tk)


def best_line(xs, ys):
    """Least-squares slope a and intercept b for ys = a*xs + b."""
    n = len(xs)
    sx, sy = sum(xs), sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    a = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    b = (sy - a * sx) / n
    return a, b


def vx_of_T(tc, r25, beta, rlin, vref, iexc, rload):
    """Sensor node voltage V(x) at temperature tc, INCLUDING the loading of the
    gain-stage input resistance (rload, = R9+R12) from node x to AGND.

    Node x: constant-current sink Iexc pulls down; the network (Rnet) feeds from
    Vref; rload bleeds V(x)/rload to ground. KCL gives:

        V(x) = (Vref - Iexc*Rnet) / (1 + Rnet/rload)

    rload -> infinity recovers the ideal  V(x) = Vref - Iexc*Rnet.
    """
    rn = rnet(tc, r25, beta, rlin)
    return (vref - iexc * rn) / (1.0 + rn / rload)


def conformity_degC(rlin, r25, beta, tlow, thigh, vref, iexc, rload, n=81):
    """Max deviation of V(x) from a straight line, in deg C, over [tlow, thigh].
    Now computed on the LOADED node voltage (see vx_of_T), so the gain-stage
    input loading is included -- this is the real in-band conformity."""
    ts = [tlow + (thigh - tlow) * i / (n - 1) for i in range(n)]
    vs = [vx_of_T(t, r25, beta, rlin, vref, iexc, rload) for t in ts]
    a, b = best_line(ts, vs)
    devs = [(v - (a * t + b)) / a for t, v in zip(ts, vs)]  # V/(V/degC)=degC
    return max(abs(d) for d in devs), list(zip(ts, devs))


def optimize_rlin(r25, beta, tlow, thigh, vref, iexc, rload, r0, span=0.5, steps=800):
    """Numerically pick Rlin for minimum loaded conformity (scans +/-span around
    the unloaded closed-form value r0). With loading, the closed-form optimum
    shifts, so we search rather than trust the formula."""
    best = (r0, float("inf"))
    for i in range(steps + 1):
        rl = r0 * (1.0 - span) + (2.0 * span * r0) * i / steps
        c, _ = conformity_degC(rl, r25, beta, tlow, thigh, vref, iexc, rload)
        if c < best[1]:
            best = (rl, c)
    return best[0]


def design(cfg):
    out = {}
    tlow, thigh = cfg["tlow"], cfg["thigh"]
    r25, beta = cfg["r25"], cfg["beta"]
    iexc, vref, rsense = cfg["iexc"], cfg["vref"], cfg["rsense"]
    rload = cfg["rload"]

    tc = 0.5 * (tlow + thigh)                      # band center
    rlin_ideal = rlin_for_center(tc, r25, beta)    # unloaded closed-form

    # excitation set resistor: Iexc = Vref / Rexc
    rexc = e96(vref / iexc)
    iexc_actual = vref / rexc
    out.update(rexc=rexc, iexc_actual=iexc_actual)

    # re-optimize Rlin for the LOADED node (closed-form optimum shifts with rload)
    rlin_opt = optimize_rlin(r25, beta, tlow, thigh, vref, iexc_actual, rload, rlin_ideal)
    rlin = e96(rlin_opt)
    out.update(tc=tc, rlin_ideal=rlin_ideal, rlin_opt=rlin_opt, rlin=rlin, rload=rload)

    # sensor NODE voltage at the band edges.
    # The network top is tied to Vref and a current sink pulls Iexc through it,
    # so the sensed node is  Vx = Vref - Iexc*Rnet.  Rnet falls as T rises, so
    # Vx RISES with temperature (same direction as the desired output).
    vx_low = vx_of_T(tlow, r25, beta, rlin, vref, iexc_actual, rload)
    vx_high = vx_of_T(thigh, r25, beta, rlin, vref, iexc_actual, rload)
    out.update(vx_low=vx_low, vx_high=vx_high)

    # output stage: Iloop = Vcmd / Rsense ; Vcmd = G * (Vx - Vzero)
    vcmd_low = 4e-3 * rsense        # 4 mA  at tlow
    vcmd_high = 20e-3 * rsense      # 20 mA at thigh
    gain = (vcmd_high - vcmd_low) / (vx_high - vx_low)   # positive (Vx rises w/ T)
    vzero = vx_low - vcmd_low / gain
    out.update(vcmd_low=vcmd_low, vcmd_high=vcmd_high, gain=gain, vzero=vzero)

    # conformity inside the band (loaded)
    cmax, table = conformity_degC(rlin, r25, beta, tlow, thigh, vref, iexc_actual, rload)
    out.update(conformity=cmax, table=table)

    # self-heating at the hot end (worst case: lowest R, most current in bead)
    # current that flows in the thermistor bead alone:
    r_bead = rt(thigh, r25, beta)
    v_net = iexc_actual * rnet(thigh, r25, beta, rlin)  # voltage across network=bead
    i_bead = v_net / r_bead
    p_bead = i_bead * v_net
    out.update(self_heat_degC=p_bead / cfg["diss"], p_bead=p_bead)

    return out


def fmt_ohm(r):
    if r >= 1e6:
        return f"{r/1e6:.3f} Mohm"
    if r >= 1e3:
        return f"{r/1e3:.3f} kohm"
    return f"{r:.1f} ohm"


def report(cfg, d):
    L = []
    p = L.append
    p("=" * 64)
    p(" Analog 4-20 mA NTC transmitter -- design report")
    p("=" * 64)
    p(f"Thermistor      : R25 = {cfg['r25']:.0f} ohm,  beta = {cfg['beta']:.0f} K")
    p(f"Mapping         : {cfg['tlow']:.1f} C -> 4 mA   |   {cfg['thigh']:.1f} C -> 20 mA")
    p(f"Band center     : {d['tc']:.1f} C")
    p("")
    p("--- Linearization ---")
    p(f"Gain-stage load : {fmt_ohm(d['rload'])} (R9+R12 on node x; large => negligible)")
    p(f"Rlin (unloaded) : {fmt_ohm(d['rlin_ideal'])}  (closed-form, ignores loading)")
    p(f"Rlin (E96)      : {fmt_ohm(d['rlin'])}   <- re-optimized for the load")
    p(f"Conformity      : +/- {d['conformity']:.3f} C  (max error vs straight line in band)")
    p("")
    p("--- Excitation ---")
    p(f"Vref            : {cfg['vref']:.3f} V (LM4040)")
    p(f"Rexc (E96)      : {fmt_ohm(d['rexc'])}   -> Iexc = {d['iexc_actual']*1e3:.4f} mA")
    p(f"Self-heating    : ~{d['self_heat_degC']*1e3:.1f} m-degC "
      f"(probe diss. const {cfg['diss']*1e3:.1f} mW/degC)")
    p("")
    p("--- Amplifier / output stage ---")
    p(f"Rsense          : {fmt_ohm(cfg['rsense'])}   (Iloop = Vcmd / Rsense)")
    p(f"Vx @ {cfg['tlow']:.0f}C       : {d['vx_low']*1e3:.1f} mV   (sensor node = Vref - Iexc*Rnet)")
    p(f"Vx @ {cfg['thigh']:.0f}C       : {d['vx_high']*1e3:.1f} mV")
    p(f"SPAN  (gain)    : {d['gain']:.4f} V/V   <- set by span pot")
    p(f"ZERO  (Vzero)   : {d['vzero']:.4f} V     <- set by zero pot")
    p(f"                  Vcmd = {d['gain']:.4f} * (Vx - Vzero),  Iloop = Vcmd / Rsense")
    p("")
    p("--- Transfer check across the band ---")
    p(f"{'T (C)':>7} {'Rt':>10} {'Rt||Rlin':>10} {'Vx(mV)':>10} {'Iloop(mA)':>10} {'err(C)':>8}")
    step = (cfg["thigh"] - cfg["tlow"]) / 8.0
    t = cfg["tlow"]
    while t <= cfg["thigh"] + 1e-6:
        rtt = rt(t, cfg["r25"], cfg["beta"])
        rn = rnet(t, cfg["r25"], cfg["beta"], d["rlin"])
        vx = vx_of_T(t, cfg["r25"], cfg["beta"], d["rlin"],
                     cfg["vref"], d["iexc_actual"], cfg["rload"])
        iloop = d["gain"] * (vx - d["vzero"]) / cfg["rsense"]
        # nearest tabulated deviation
        err = min(d["table"], key=lambda te: abs(te[0] - t))[1]
        p(f"{t:7.1f} {rtt:10.0f} {rn:10.0f} {vx*1e3:10.1f} {iloop*1e3:10.2f} {err:+8.3f}")
        t += step
    p("=" * 64)
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    for k, v in DEFAULTS.items():
        ap.add_argument(f"--{k}", type=float, default=v)
    cfg = vars(ap.parse_args())
    d = design(cfg)
    print(report(cfg, d))


if __name__ == "__main__":
    main()
