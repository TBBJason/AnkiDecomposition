# Does decomposition actually work?

Experimental design for the project's central claim, and an honest account of why it is
harder than it looks.

**Is the additive design possible?** Yes — and it is better than the held-out-probe design
I proposed earlier, on four independent counts. It is also *safer to build*. Details in
section 3.

---

## 1. What the literature says

**Firmly established:** the spacing effect. Spacing beat cramming in
[259 of 271 comparisons](https://acemedboards.com/flashcard-spaced-repetition/), with
medical-education meta-analysis showing SMD ≈ 0.78. Not in question.

**Asserted but untested:** the minimum information principle. Wozniak's
[twenty rules](https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge)
state it forcefully and every flashcard guide repeats it, but there appears to be **no
direct randomised test of decomposing flashcards** measuring retention of the original
knowledge.

**Cuts against pure decomposition:**
[Lim, Reiser & Olina](https://knilt.arcc.albany.edu/images/6/6a/Lim_etal_ETR&D_2009.pdf)
found the **whole-task group significantly outperformed the part-task group** on both
acquisition and transfer. Parts learned in isolation do not reliably assemble into a
whole.

### The orchestrator card is the literature's own remedy

This is the important finding, and it supports the orchestrator more strongly than the
evidence supports plain decomposition.

- [Wightman's work on multistep procedural tasks](https://pubmed.ncbi.nlm.nih.gov/11132799/)
  found that **when total training trials were equated**, forward chaining that included
  practice with *concurrent* responses transferred to whole-task performance as well as
  whole-task training, and **better than pure part-task training**. Part-task practice
  plus integration practice beats part-task practice alone.
- The [part-task training meta-analysis](https://www.researchgate.net/publication/236926003_Effectiveness_of_Part-Task_Training_and_Increasing-Difficulty_Training_Strategies_A_Meta-Analysis_Approach)
  concludes part-task training succeeds when the integrated parts are varied in the
  priority given to the learner — integration is the active ingredient.
- Van Merriënboer's [4C/ID model](https://www.researchgate.net/publication/225798787_Blueprints_for_complex_learning_The_4CID-model)
  prescribes exactly this combination: whole learning tasks **and** part-task practice as
  distinct, co-present components. Part-task practice is never the whole design.

So the three-tier structure — atoms, orchestrator, original — maps onto an established
instructional design framework. **Atoms alone is the configuration the literature is
sceptical of; atoms plus integration is the configuration it supports.** Adding the
orchestrator moves the project from the weakly-supported hypothesis to the
better-supported one.

One condition attached: Wightman's benefit held **when total practice was equated.** That
constraint drives the outcome measure in section 5.

### Likely real answer

Not yes/no but **"for which cards?"** — probably yes for genuinely high
element-interactivity compound cards, neutral-to-harmful for cards that were already
atomic. Identifying *which* is more valuable than a global verdict, and feeds straight
back into the triage classifier.

---

## 2. Confounds

| # | Confound | Why it fools you | Status in additive design |
|---|---|---|---|
| 1 | **Regression to the mean** | Cards are selected at their worst; they improve regardless. | Handled by randomisation |
| 2 | **Tautological outcome** | Atoms are easier questions; their high accuracy proves nothing. | **Eliminated** — outcome is the original card, identical in both arms |
| 3 | **Extra exposure at the gate** | Reading the proposal is itself studying. | Needs an active control |
| 4 | **Unequal time on task** | Treatment gets ~5 cards vs 1, so several times the study time. | **Dominant threat.** See §5 |
| 5 | **Selective acceptance** | You accept good proposals, reject bad ones. | Handled by intent-to-treat |
| 6 | **Novelty / Hawthorne** | New-tool enthusiasm inflates early results. | Partly handled by active control |
| 7 | **Time-varying context** | Exam season, sleep, workload. | Handled by randomisation |

The additive design kills #2 outright, which was fatal to the obvious approach. In
exchange, #4 becomes the dominant problem.

---

## 3. The additive design

**Treatment:** keep the original card in rotation, and add beneath it
- 2–5 **atomic cards** (one fact each)
- 1 **orchestrator card** testing how the atoms assemble

**Control:** keep the original card in rotation, add nothing.

**Outcome:** measured on the **original card**, which stays active in both arms.

### Why this is better than the probe design

1. **The outcome measure is honest.** The original card is the same question in both arms,
   so you are comparing like with like. No artificial held-out probe.
2. **Twice the statistical power** (§5). The original keeps earning natural reviews in
   both arms, so every review is an observation instead of 3 artificial probes.
3. **Ecologically valid.** It tests what the product actually does, under normal study
   conditions.
4. **Far safer to build.** This is the underrated one: the additive design performs **no
   scheduling surgery**. Nothing is suspended, replaced, promoted, or restored. You only
   ever *add* cards and observe an existing one. The entire dangerous part of M3 — the
   suspend/unsuspend state machine, promote-back logic, rollback of scheduling state —
   largely disappears. Much of the project's implementation risk was in code this design
   does not need.

### Define the orchestrator precisely, or it will test nothing

The risk: if the orchestrator asks essentially what the original card asks, you have
created a **sibling interference pair** — two cards testing the same whole — which is the
exact failure mode the triage classifier is supposed to detect. You would be
manufacturing the problem you set out to fix.

The orchestrator must test **assembly**, not re-enumeration:

| Tier | Tests | Example (facial nerve branches) |
|---|---|---|
| Atoms | Individual facts | "Which facial nerve branch supplies the frontalis?" → Temporal |
| **Orchestrator** | **Structure, order, relation, organising principle** | "In what order do the five facial nerve branches run, superior to inferior?" / "What mnemonic organises them?" |
| Original | Full composite recall — the target and the outcome measure | "Name the five branches of the facial nerve" |

Good orchestrator forms: ordering/sequencing, the organising principle or mnemonic,
how parts relate causally, which part is the exception, what breaks if one part is
missing. Bad orchestrator forms: a reworded version of the original, or a list-completion
card that is the original minus one item.

A practical rule: **if the orchestrator's answer is the same set as the original's answer,
rewrite it.** It should ask about *relations between* the atoms, not their identity.

### Generating the orchestrator

This is a distinct LLM task from decomposition and deserves its own prompt. Decomposition
splits; orchestration finds the structure linking the pieces. Expect orchestrator quality
to be the weak link — "what is the organising principle here?" is a harder generation
problem than "split this list," and some cards have no interesting structure at all. The
generator must be allowed to return **no orchestrator** rather than inventing a spurious
one, and the review gate should make rejecting it easy.

### Arms

Minimum viable, two arms:

- **A — control:** original card only.
- **B — treatment:** original + atoms + orchestrator.

This answers the product question: *should the add-on do this?*

If you later want the mechanistic question — is it the structure or just the extra time? —
add:

- **C — time-matched control:** original card only, reviewed more frequently so total
  study time matches arm B.
- **D — atoms only, no orchestrator:** isolates the orchestrator's specific contribution.

Arm D is the scientifically interesting one given the literature, since atoms-alone is
precisely the configuration the part-task research questions. But each arm costs power.
Start with A/B; add D only when pooling across users.

Randomise **before the user sees the proposal**, stratified by deck and by
`proposed_atom_count`, and log the assignment immediately so intent-to-treat stays
possible.

---

## 4. Power

From `m0_triage/power_additive_design.py` (Monte Carlo, card-level clustered analysis):

**Cards per arm for 80% power, α = 0.05, by number of observed reviews of the original
card (k):**

| Effect on original card | k=1 | k=3 | k=6 | k=12 | k=20 |
|---|---|---|---|---|---|
| +10pp (0.45→0.55) | 520 | 220 | 150 | 100 | 90 |
| +15pp (0.45→0.60) | 230 | 100 | 70 | 50 | 40 |
| +20pp (0.45→0.65) | 130 | 60 | 40 | 30 | 30 |

A card on a normal schedule over a six-month window is seen roughly 6–20 times, so the
realistic range is the right-hand columns.

**Against the probe design**, detecting +15pp:

| Design | Cards per arm |
|---|---|
| Probe (k=3 artificial probes) | 100 |
| **Additive (k=12 natural reviews)** | **50** |

**Halves the required collection size.** Combined with the feasibility table:

| Collection | Leeches | Decomposable | Per arm |
|---|---|---|---|
| Casual, 3k | ~150 | ~37 | ~18 |
| Serious, 10k | ~700 | ~210 | ~105 |
| Med student, 25k | ~2,000 | ~700 | ~350 |

A 10k-card collection at ~105/arm is **adequately powered for +15pp and marginal for
+10pp**. That is a genuinely answerable single-user experiment, which the probe design
was not.

---

## 5. The time-on-task problem

Treatment adds ~4 cards against a control that adds none. The treatment arm receives
several times the study time on that knowledge. **Raw recall will favour treatment for
that reason alone, and such a result is nearly uninformative** — "studying something five
times as much improves recall" needs no experiment.

Three responses, in increasing rigour:

1. **Efficiency as the primary outcome.** Recall on the original card **per minute
   invested in the whole lineage** (original + atoms + orchestrator), with review time
   summed from `revlog`. Requires no extra arms, and efficiency is the decision-relevant
   quantity anyway: an intervention that works but costs 5× the time is not obviously
   worth shipping.
2. **Cap the added review budget** so the lineage's total daily time approximates the
   original card's historical rate. More invasive, but makes raw recall interpretable.
3. **Time-matched control arm (C).** The rigorous answer, at the cost of a third of your
   power.

**Recommendation:** efficiency as primary, raw recall as a clearly-labelled secondary.
This also connects the experiment to Wightman's result, which held specifically under
equated training trials — matching on time is what makes your result comparable to the
literature rather than a separate and weaker claim.

### Outcomes

**Primary:** recall probability on the original card, offset by log cumulative lineage
study minutes. Equivalently: minutes invested to reach a fixed retention level.

**Secondary:**
- Raw recall on the original card (repeated measures, labelled as not time-adjusted)
- FSRS stability of the original card, log-transformed
- Cumulative seconds to criterion (original correct on 3 consecutive reviews)
- Re-leech rate within 180 days
- Total review burden added per card
- **Orchestrator-specific:** does arm B beat arm D? Only answerable with the fourth arm,
  but record everything needed so a later pooled analysis can ask it.

---

## 6. What to record

**Anki already logs the hard part.** `revlog` holds every review with timestamp, grade,
interval, and milliseconds taken. All outcome data comes free; the add-on only records
intervention metadata.

```sql
CREATE TABLE intervention (
  id                INTEGER PRIMARY KEY,
  original_card_id  INTEGER NOT NULL,   -- stays active; this is the outcome measure
  original_note_id  INTEGER NOT NULL,
  assigned_arm      TEXT    NOT NULL,   -- 'control'|'full'|'atoms_only'|'time_matched'
  assigned_at       INTEGER NOT NULL,
  rng_seed          INTEGER NOT NULL,
  stratum           TEXT    NOT NULL,
  -- triage snapshot
  failure_mode      TEXT,
  value_rating      TEXT,
  triage_confidence REAL,
  proposed_atoms    INTEGER,
  -- provenance
  model_id          TEXT,
  prompt_version    TEXT,
  orchestrator_prompt_version TEXT,
  -- intent-to-treat
  gate_action       TEXT,               -- 'accepted'|'edited'|'rejected'|'timeout'
  gate_action_at    INTEGER,
  orchestrator_accepted INTEGER,        -- separately rejectable
  -- baseline on the original card, frozen at assignment
  baseline_lapses   INTEGER,
  baseline_reps     INTEGER,
  baseline_time_ms  INTEGER,
  baseline_fsrs_d   REAL,
  baseline_fsrs_s   REAL
);

-- Added cards. tier distinguishes atoms from the orchestrator.
CREATE TABLE added_card (
  id              INTEGER PRIMARY KEY,
  intervention_id INTEGER NOT NULL REFERENCES intervention(id),
  card_id         INTEGER NOT NULL,
  note_id         INTEGER NOT NULL,
  tier            TEXT    NOT NULL,     -- 'atom' | 'orchestrator'
  tier_index      INTEGER,              -- atom ordering
  was_edited      INTEGER NOT NULL DEFAULT 0,
  orchestrator_kind TEXT,               -- 'sequence'|'principle'|'relation'|'exception'
  created_at      INTEGER NOT NULL
);

CREATE TABLE state_change (
  id              INTEGER PRIMARY KEY,
  intervention_id INTEGER NOT NULL REFERENCES intervention(id),
  from_state      TEXT,
  to_state        TEXT    NOT NULL,
  at              INTEGER NOT NULL,
  reason          TEXT
);
```

Note what is **absent** versus the earlier schema: no `probe` table, and `state_change`
shrinks dramatically. The additive design needs far less bookkeeping because it never
mutates scheduling state.

Outcomes are computed by joining `revlog` against `original_card_id` (the outcome) and
`added_card` (the time cost). Mirror provenance into note fields as well, so lineage
survives sync to mobile clients.

---

## 7. Analysis plan

**Pre-register before collecting a single card.** Hypotheses, primary outcome, model,
stopping rule, in a dated file you do not edit afterwards. One hour of work, and the
difference between a result and a story — the pull toward re-cutting the data until
decomposition looks good will be strong, because you want it to work.

**Primary model** — mixed-effects logistic regression on original-card reviews:

```
correct ~ arm + log(cumulative_lineage_minutes)
          + baseline_fsrs_d + review_index
          + (1 | deck) + (1 | original_card_id)
```

The time term is what converts this from "treatment got more practice" to "treatment used
practice better." Intent-to-treat on `assigned_arm`; per-protocol on `gate_action` as a
labelled secondary.

**Prefer Bayesian estimation.** At n ≈ 100/arm, a posterior over the effect size with a
credible interval is more honest than a p-value and degrades gracefully: "probably a small
benefit, cannot exclude zero" is a legitimate output, whereas a null p-value invites
misreading as "no effect."

**Pre-specified moderators** — the question you actually care about:

```
correct ~ arm * proposed_atoms + arm * failure_mode + arm * orchestrator_kind + ...
```

If decomposition helps 5-fact cards but not 2-fact ones, or if `sequence` orchestrators
work and `principle` ones do not, that is the finding — and it feeds directly into the
triage classifier's thresholds.

**Survival analysis** for time-to-criterion (Cox model on cumulative study seconds).

---

## 8. Honest limits

- **Time-on-task is only ever adjusted for, never eliminated**, without the time-matched
  arm. Statistical adjustment assumes the functional form is right.
- **The orchestrator's specific contribution is not identified** in a two-arm design. A/B
  tells you the package works; only arm D isolates the orchestrator.
- **n binds.** A single collection detects large effects, not subtle ones.
- **No generalisation from one user** — your subject matter, card-writing habits, memory.
- **The result may be null or negative.** A credible null is still a real contribution,
  and far better than a confounded positive.
- **Long timeline.** With a six-month observation window the first trustworthy answer is
  ~6–8 months out. Interim peeking inflates false positives unless you pre-specify a
  correction.
- **FSRS needed** for stability-based secondary outcomes.

---

## 9. Build order

Build the experiment *into* the pipeline; retrofitting makes early data unusable.

| Stage | Work |
|---|---|
| **M0** | Run both power scripts with your own decomposable count. Decide whether the RCT is viable for your collection. |
| **M1** | Sidecar schema. Record baselines on candidate cards immediately — free, and impossible to reconstruct later. |
| **M2** | Decomposition **and** orchestrator generation, each with its own prompt and its own accept/reject control at the gate. Randomisation logged pre-reveal. |
| **M3** | Much smaller than previously planned: link added cards to the original, enforce review budgets, log state changes. No scheduling surgery. |
| **M4** | Export to CSV/Parquet + analysis notebook. Keep stats out of the add-on. |
| **M5** | Pre-register, wait out the window, analyse, publish either way. |

Keep analysis code in a separate `analysis/` directory with its own dependencies (pandas,
statsmodels or pymc, lifelines). The add-on itself should ship **no** scientific Python —
Anki bundles its own interpreter and heavy dependencies reliably break installs.

---

## 10. Why this is the most valuable part of the project

Decomposition is a few LLM calls; a competitor clones it in a weekend. The pedagogical
lore underneath it has, as far as I can find, never been directly tested, and the adjacent
literature is ambivalent about decomposition *without* integration.

The orchestrator addition is what makes the hypothesis defensible rather than folk wisdom
— it is the configuration 4C/ID and the progressive-part-training results actually
support. **A credible answer to "does this work, and for which cards?" is a genuine
contribution**: publishable, defensible, and something no competitor has. It also makes
the product honest, because the triage classifier can eventually recommend decomposition
from measured effect by card type rather than from a 1999 principle nobody checked.

Build the measurement apparatus first. It is the moat.
