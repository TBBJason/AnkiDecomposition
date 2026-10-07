#!/usr/bin/env python3
#
# AnkiDecomposition - https://github.com/TBBJason/AnkiDecomposition
# Copyright (C) 2026 AnkiDecomposition contributors
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version. See the LICENSE file in the project root, or
# <https://www.gnu.org/licenses/>.
"""
How many cards do you need to answer "does decomposition work?"

Monte Carlo power analysis for the decomposition RCT. Pure standard library so
it runs anywhere. The point is to find out *before* building the experiment
whether a single user's collection can possibly answer the question.

Two outcome types are compared, because the choice matters enormously:
  - binary:     did the learner recall the probe card at the 60-day horizon?
  - continuous: FSRS stability (log days) of the probe card.

Continuous outcomes carry far more information per card, so they need far fewer
cards. That is the single most important design lever available.
"""

import math
import random

Z_CRIT = 1.959963984540054  # two-sided alpha = 0.05
N_SIMS = 4000


# ------------------------------------------------------------------ stats

def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def two_proportion_power(p_ctrl, p_treat, n_per_arm, rng):
    """Monte Carlo power for a two-proportion z-test."""
    hits = 0
    for _ in range(N_SIMS):
        x1 = sum(1 for _ in range(n_per_arm) if rng.random() < p_ctrl)
        x2 = sum(1 for _ in range(n_per_arm) if rng.random() < p_treat)
        phat1 = x1 / float(n_per_arm)
        phat2 = x2 / float(n_per_arm)
        pool = (x1 + x2) / float(2 * n_per_arm)
        se = math.sqrt(pool * (1.0 - pool) * (2.0 / n_per_arm))
        if se == 0:
            continue
        if abs((phat2 - phat1) / se) > Z_CRIT:
            hits += 1
    return hits / float(N_SIMS)


def continuous_power(effect_d, n_per_arm, rng):
    """Monte Carlo power for a two-sample test on a standardised effect size."""
    hits = 0
    for _ in range(N_SIMS):
        a = [rng.gauss(0.0, 1.0) for _ in range(n_per_arm)]
        b = [rng.gauss(effect_d, 1.0) for _ in range(n_per_arm)]
        ma, mb = sum(a) / n_per_arm, sum(b) / n_per_arm
        va = sum((x - ma) ** 2 for x in a) / (n_per_arm - 1)
        vb = sum((x - mb) ** 2 for x in b) / (n_per_arm - 1)
        se = math.sqrt(va / n_per_arm + vb / n_per_arm)
        if se == 0:
            continue
        if abs((mb - ma) / se) > Z_CRIT:
            hits += 1
    return hits / float(N_SIMS)


def analytic_n_binary(p_ctrl, p_treat, power=0.80):
    """Closed-form n per arm, as a sanity check on the simulation."""
    z_b = {0.80: 0.8416, 0.90: 1.2816}[power]
    pbar = (p_ctrl + p_treat) / 2.0
    num = (Z_CRIT * math.sqrt(2 * pbar * (1 - pbar)) +
           z_b * math.sqrt(p_ctrl * (1 - p_ctrl) + p_treat * (1 - p_treat))) ** 2
    return int(math.ceil(num / (p_treat - p_ctrl) ** 2))


def analytic_n_continuous(d, power=0.80):
    z_b = {0.80: 0.8416, 0.90: 1.2816}[power]
    return int(math.ceil(2 * ((Z_CRIT + z_b) / d) ** 2))


# ------------------------------------------------------------------ report

def main():
    rng = random.Random(7)

    print("")
    print("=" * 74)
    print("  POWER ANALYSIS: decomposition RCT")
    print("=" * 74)
    print("""
  Assumed baseline: a learner recalls the composite probe card 45% of the
  time at the 60-day horizon in the control arm. We ask how many cards per
  arm are needed to detect various improvements at 80% power, alpha 0.05.
""")

    print("  BINARY OUTCOME (probe recalled: yes/no)")
    print("  " + "-" * 70)
    print("  {:>12} {:>10} {:>14} {:>14}".format(
        "improvement", "treat p", "n/arm (sim)", "n/arm (exact)"))
    print("  " + "-" * 70)

    p_ctrl = 0.45
    for delta in (0.05, 0.10, 0.15, 0.20, 0.25):
        p_treat = p_ctrl + delta
        n_exact = analytic_n_binary(p_ctrl, p_treat)
        # Find simulated n reaching 80% power, searching a sensible grid.
        n_sim = None
        for n in range(20, 2200, 20):
            if two_proportion_power(p_ctrl, p_treat, n, rng) >= 0.80:
                n_sim = n
                break
        print("  {:>11}pp {:>10.2f} {:>14} {:>14}".format(
            int(delta * 100), p_treat,
            n_sim if n_sim else ">2200", n_exact))

    print("")
    print("  CONTINUOUS OUTCOME (FSRS stability of probe, log days)")
    print("  " + "-" * 70)
    print("  {:>12} {:>12} {:>14} {:>14}".format(
        "effect size", "label", "n/arm (sim)", "n/arm (exact)"))
    print("  " + "-" * 70)

    for d, label in ((0.2, "small"), (0.3, "small-mod"),
                     (0.5, "moderate"), (0.8, "large")):
        n_exact = analytic_n_continuous(d)
        n_sim = None
        for n in range(10, 900, 10):
            if continuous_power(d, n, rng) >= 0.80:
                n_sim = n
                break
        print("  {:>12.1f} {:>12} {:>14} {:>14}".format(
            d, label, n_sim if n_sim else ">900", n_exact))

    # ---------------------------------------------------------- feasibility
    print("")
    print("=" * 74)
    print("  WHAT THIS MEANS FOR A SINGLE COLLECTION")
    print("=" * 74)

    scenarios = [
        ("Serious user, 10k cards", 10000, 0.07, 0.30),
        ("Med student, 25k cards", 25000, 0.08, 0.35),
        ("Casual user, 3k cards", 3000, 0.05, 0.25),
    ]

    print("")
    print("  {:<26} {:>8} {:>9} {:>11} {:>10}".format(
        "scenario", "leeches", "decomp.", "per arm (3)", "per arm (2)"))
    print("  " + "-" * 70)
    for name, total, leech_rate, decomp_rate in scenarios:
        leeches = int(total * leech_rate)
        decomposable = int(leeches * decomp_rate)
        print("  {:<26} {:>8} {:>9} {:>11} {:>10}".format(
            name, leeches, decomposable,
            decomposable // 3, decomposable // 2))

    print("""
  Read that against the tables above.

  With roughly 60-120 cards per arm, a single collection can detect:
    - binary outcome ...... only very large effects (20-25pp), unreliably
    - continuous outcome .. moderate effects (d = 0.5), adequately

  Conclusions that follow directly:

  1. USE A CONTINUOUS OUTCOME as primary. FSRS stability on the probe card,
     or cumulative study seconds to criterion. A binary recalled/forgotten
     outcome throws away so much information that a single user cannot
     realistically answer the question with it.

  2. TWO ARMS, NOT THREE, for a single user. A three-arm design is cleaner
     scientifically but costs you a third of your power. Run
     decompose-vs-active-control first; add the third arm only if pooling
     data across users.

  3. PREFER REPEATED MEASURES. Probing the same card at 30/60/90 days and
     modelling it with random effects per card recovers a substantial amount
     of the power lost to small n. This is effectively free - it is just
     extra scheduled probes.

  4. A SINGLE USER ANSWERS A NARROW QUESTION: "does this help me, a lot?"
     The general question needs pooled, opt-in, multi-user data. Design the
     schema for that from the start even if you never ship it.
""")


if __name__ == "__main__":
    main()
