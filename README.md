# AnkiDecomposition

An Anki add-on that finds the cards you keep forgetting, works out *why*, and for the ones
worth saving, builds a scaffold beneath them — atomic cards for the individual facts plus
an **orchestrator card** that tests how those facts fit together.

The original card stays in rotation the whole time. It is never replaced, and it is the
thing we measure.

> **Status: design and measurement stage.** No add-on code yet. What exists is the
> research design and a set of throwaway tools to answer the question that decides whether
> the add-on is worth building at all.

---

## The idea in one picture

| Tier | Tests | Example — facial nerve branches |
| --- | --- | --- |
| **Atoms** | One fact each | *"Which facial nerve branch supplies the frontalis?"* → Temporal |
| **Orchestrator** | Structure: order, organising principle, relations, exceptions | *"In what order do the five branches run, superior to inferior?"* |
| **Original** | Full composite recall — the target, and the outcome measure | *"Name the five branches of the facial nerve"* |

The intervention is **additive**. Nothing is suspended, replaced, promoted, or restored.
That is deliberate on two counts: it is the configuration the instructional-design
literature actually supports, and it avoids all scheduling surgery, which was the riskiest
code in the original plan.

---

## Why this might not work

Stated up front, because the project's value depends on taking it seriously.

The folk wisdom behind flashcard decomposition is the **minimum information principle** —
one fact per card. It is repeated in every flashcard guide. As far as we can find, it has
**never been directly tested** on flashcards.

Worse, the adjacent literature is ambivalent. In part-task vs. whole-task training
research, [Lim, Reiser & Olina](https://knilt.arcc.albany.edu/images/6/6a/Lim_etal_ETR&D_2009.pdf)
found the **whole-task group significantly outperformed the part-task group** on both
acquisition and transfer. Parts learned in isolation do not reliably assemble into a whole.

The orchestrator tier exists to address exactly that. Part-task practice *plus* integration
practice is a much better-supported configuration:

- [Wightman, multistep procedural tasks](https://pubmed.ncbi.nlm.nih.gov/11132799/) — with
  total training trials equated, part-task practice including integration matched
  whole-task training and beat pure part-task training.
- [Van Merriënboer's 4C/ID model](https://www.researchgate.net/publication/225798787_Blueprints_for_complex_learning_The_4CID-model)
  — prescribes whole learning tasks and part-task practice as distinct, co-present
  components.
- [Part-task training meta-analysis](https://www.researchgate.net/publication/236926003_Effectiveness_of_Part-Task_Training_and_Increasing-Difficulty_Training_Strategies_A_Meta-Analysis_Approach)
  — part-task training works when integration of the parts is prioritised.

So the hypothesis under test is not "splitting cards is good." It is: **atoms plus an
integration card improve recall of the original composite knowledge, per minute invested.**

---

## Repository layout

| Path | What it is |
| --- | --- |
| [`ROADMAP.md`](ROADMAP.md) | Design stance, non-negotiable constraints, milestones M0–M5, open questions, prior art |
| [`EXPERIMENT.md`](EXPERIMENT.md) | The randomised design: confound analysis, arms, outcome measures, power, data schema, analysis plan |
| [`m0_triage/`](m0_triage/) | Standalone measurement tools. Not an add-on — deliberately throwaway |

### `m0_triage/` contents

| File | Purpose |
| --- | --- |
| `extract_candidates.py` | Read-only extractor. Ranks your struggling cards by **real time cost** from Anki's review log |
| `triage_prompt.md` | Two-axis triage rubric — failure mode × value. Usable as LLM prompt *and* manual labelling guide |
| `power_analysis.py` | Monte Carlo power analysis for the held-out-probe design |
| `power_additive_design.py` | Power analysis for the additive design actually adopted |
| `make_test_collection.py` | Synthetic collection generator, so the tools can be tested without touching real data |
| `README.md` | Safety steps, per-OS instructions, column reference |

---

## Start here

The first question is not "how do I build this" but **"how many of my cards would actually
benefit?"** If the answer is under ~15%, this is a triage tool, not a decomposition tool,
and that is a far cheaper thing to build.

```bash
# 1. Close Anki, then copy your collection (never work on the live file)
cp ~/.local/share/Anki2/User\ 1/collection.anki2 /tmp/col-copy.anki2

# 2. Rank your struggling cards by time cost
python3 m0_triage/extract_candidates.py /tmp/col-copy.anki2 --outdir out

# 3. Check whether an experiment is even viable at your collection size
python3 m0_triage/power_additive_design.py
```

Needs only the Python 3 standard library. Full instructions, including Windows and macOS
paths, in [`m0_triage/README.md`](m0_triage/README.md).

Then hand-label your top 40 candidates using `triage_prompt.md` **before** looking at any
LLM output, and compare. Your labels are the ground truth.

---

## Decision gates

The roadmap is built around gates rather than features, because several of them can kill
or redirect the project cheaply:

| Gate | Question | If it fails |
| --- | --- | --- |
| **M0a** | What fraction of your leeches are genuinely decomposable? | Under 15% → build a triage tool instead |
| **M0b** | Can an LLM write a *non-redundant* orchestrator? | Rethink the middle tier before building on it |
| **M0c** | Is the experiment powered at your collection size? | Report descriptively; do not claim causality |
| **M1** | Do triage labels match your own judgment? | Fix the prompt before writing any pipeline |
| **M2** | Do generated atoms survive review unedited ~70% of the time? | Generation is not ready |

---

## Known risks

- **Time-on-task.** Treatment adds ~4 cards; control adds none. Raw recall will favour
  treatment for that reason alone. The primary outcome must therefore be **efficiency** —
  recall per minute invested across the lineage.
- **Orchestrator redundancy.** If the orchestrator's answer is the same set as the
  original's, it is a duplicate and creates sibling interference — the exact failure mode
  triage exists to detect. Enforced as a validation step, not left to the prompt.
- **Statistical power.** A ~10k-card collection gives roughly 105 cards per arm: adequate
  for a 15-percentage-point effect, marginal for 10. A 3k-card collection cannot answer
  this at all.
- **Timeline.** A six-month observation window means the first trustworthy answer is
  6–8 months out.
- **The result may be null or negative.** Given the part-task literature, that is a real
  possibility. A credible null is still a useful contribution, and much better than a
  confounded positive.

---

## Prior art

No existing add-on does the full loop, but every individual piece exists and is worth
studying before writing code:

| Project | Overlap |
| --- | --- |
| [AnkiAIUtils](https://github.com/thiswillbeyourgithub/AnkiAIUtils) | Closest in spirit — auto-enhances failed cards with explanations and mnemonics. Author has asked for help packaging it as an add-on |
| [anki-bury-explain](https://github.com/TheLycoi/anki-bury-explain) | Same trigger: after repeated fails, opens an AI with a card-formulation audit |
| [Leech Toolkit](https://github.com/iamjustkoi/LeechToolkit) | Leech lifecycle, including reverting leech status |
| [Trigger Action on Note](https://ankiweb.net/shared/info/1981494159) | Maturity-gated card visibility — a ready-made gating primitive |
| [anki-skill](https://github.com/djt97/anki-skill) | Cost-based deck health metric |
| [card-janitor](https://github.com/zarnthyr/card-janitor) | Policy-based lifecycle actions |

---

## License

[AGPL-3.0](LICENSE). Anki is AGPL-3.0 and add-ons extend the desktop application, so
Anki's guidance is that add-ons must be AGPL-3.0 or a compatible licence — and that an
unlicensed add-on is assumed to be AGPL-3.0.

---

*Some reference material above was paraphrased and condensed for compliance with content
licensing restrictions. Follow the links for the original sources.*
