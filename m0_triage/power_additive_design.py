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
Power analysis for the ADDITIVE design.

Design under test:
  treatment = keep the original card + add atomic cards + add an orchestrator card
  control   = keep the original card, add nothing

The outcome is measured on the ORIGINAL card, which stays in normal rotation in
both arms. That is the key structural advantage: instead of 3 artificial probes
per card, you get every natural review of the original card as an observation.

This script quantifies how much that repeated-measures structure buys you.

Analysis simulated is the robust, simple one: collapse each card to its own
proportion-correct, then compare arms at the card level. This respects the
clustering (reviews within a card are correlated) without needing a mixed-model
library, and it is what you should run as a primary analysis anyway.

Pure standard library.
"""

import math
import random

Z_CRIT = 1.959963984540054
N_SIMS = 3000


def logit(p):
    return math.log(p / (1.0 - p))


def inv_logit(x):
    if x > 36:
        return 1.0
    if x < -36:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def welch_reject(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return False
    ma, mb = sum(a) / na, sum(b) / nb
    va = sum((x - ma) ** 2 for x in a) / (na - 1)
    vb = sum((x - mb) ** 2 for x in b) / (nb - 1)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return False
    return abs((mb - ma) / se) > Z_CRIT


def power_repeated(n_cards, k_reviews, p_ctrl, delta_logit, tau, rng):
    """
    n_cards      cards per arm
    k_reviews    observations of the original card per card over the window
    p_ctrl       marginal recall probability in control
    delta_logit  treatment effect on the log-odds scale
    tau          SD of the per-card random intercept (card heterogeneity)
    """
    base = logit(p_ctrl)
    hits = 0
    for _ in range(N_SIMS):
        arm_means = ([], [])
        for arm, shift in ((0, 0.0), (1, delta_logit)):
            for _c in range(n_cards):
                ability = base + shift + rng.gauss(0.0, tau)
                p = inv_logit(ability)
                correct = sum(1 for _ in range(k_reviews) if rng.random() < p)
                arm_means[arm].append(correct / float(k_reviews))
        if welch_reject(arm_means[0], arm_means[1]):
            hits += 1
    return hits / float(N_SIMS)


def find_n(k_reviews, p_ctrl, delta_logit, tau, rng, target=0.80, cap=600):
    for n in range(20, cap + 1, 10):
        if power_repeated(n, k_reviews, p_ctrl, delta_logit, tau, rng) >= target:
            return n
    return None


def main():
    rng = random.Random(11)
    p_ctrl = 0.45
    tau = 0.8   # moderate card-to-card heterogeneity

    print("")
    print("=" * 76)
    print("  ADDITIVE DESIGN: original card kept in both arms, measured directly")
    print("=" * 76)
    print("""
  Control recall on the original card: 45%.
  Cards per arm needed for 80% power, alpha 0.05, by number of natural
  reviews of the original card observed during the study window.
""")

    deltas = [
        (logit(0.55) - logit(0.45), "+10pp (0.45 -> 0.55)"),
        (logit(0.60) - logit(0.45), "+15pp (0.45 -> 0.60)"),
        (logit(0.65) - logit(0.45), "+20pp (0.45 -> 0.65)"),
    ]

    header = "  {:<24}".format("effect") + "".join(
        "{:>12}".format("k=%d" % k) for k in (1, 3, 6, 12, 20))
    print(header)
    print("  " + "-" * 72)

    for delta, label in deltas:
        cells = []
        for k in (1, 3, 6, 12, 20):
            n = find_n(k, p_ctrl, delta, tau, rng)
            cells.append("{:>12}".format(n if n else ">600"))
        print("  {:<24}".format(label) + "".join(cells))

    print("""
  k = number of observed reviews of the original card per card.

  A card reviewed on a normal schedule over a 6-month study window will
  typically be seen somewhere between 6 and 20 times, depending on its
  interval. So the realistic operating range is k = 6-20, i.e. the right-hand
  columns.
""")

    # ------------------------------------------------- comparison to probes
    print("=" * 76)
    print("  WHY THIS BEATS THE HELD-OUT PROBE DESIGN")
    print("=" * 76)

    delta15 = logit(0.60) - logit(0.45)
    n_probe = find_n(3, p_ctrl, delta15, tau, rng)      # 3 probes at 30/60/90d
    n_natural = find_n(12, p_ctrl, delta15, tau, rng)   # natural rotation

    print("""
  Detecting a +15pp improvement on the original card:

    probe design   (k=3  artificial probes) ...... {} cards per arm
    additive design (k=12 natural reviews) ....... {} cards per arm

  Reduction in required collection size: {:.0%}

  The additive design extracts far more information per card because the
  original card keeps earning reviews in both arms. Nothing is held out,
  so nothing is wasted.
""".format(n_probe if n_probe else ">600",
           n_natural if n_natural else ">600",
           (1 - n_natural / float(n_probe)) if (n_probe and n_natural) else 0))

    # ------------------------------------------------- feasibility
    print("=" * 76)
    print("  FEASIBILITY BY COLLECTION SIZE")
    print("=" * 76)
    print("")
    print("  {:<28} {:>9} {:>13} {:>12}".format(
        "collection", "leeches", "decomposable", "per arm"))
    print("  " + "-" * 66)
    for name, total, lr, dr in (
        ("Casual, 3k cards", 3000, 0.05, 0.25),
        ("Serious, 10k cards", 10000, 0.07, 0.30),
        ("Med student, 25k cards", 25000, 0.08, 0.35),
    ):
        leeches = int(total * lr)
        dec = int(leeches * dr)
        print("  {:<28} {:>9} {:>13} {:>12}".format(
            name, leeches, dec, dec // 2))

    print("""
  Against the k=12 row above, a 10k-card collection (~105 per arm) is
  adequately powered for a +15pp effect, and marginal for +10pp. That is a
  real, answerable experiment on a single collection - which the probe
  design was not.

  CAVEAT THAT DOMINATES EVERYTHING ELSE
  -------------------------------------
  Treatment adds ~4 extra cards (3 atoms + 1 orchestrator) against a control
  that adds none. The treatment arm therefore receives several times the
  study time. Raw recall WILL favour treatment for that reason alone, and
  such a result is close to uninformative.

  Report efficiency - recall per minute invested on the lineage - as the
  primary outcome. Note that the strongest supporting result in the
  part-task literature (Wightman, forward chaining with concurrent practice)
  held specifically when total training trials were EQUATED. Matching on
  time is what connects your experiment to that literature.
""")


if __name__ == "__main__":
    main()
