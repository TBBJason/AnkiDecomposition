# Anki Adaptive Decomposition Add-on — Roadmap

Working name: **Scaffold**. Detects struggling cards, and for the ones worth saving, adds
a three-tier scaffold beneath them with an LLM — atomic cards for the individual facts,
plus an **orchestrator card** that tests how those facts assemble. The original card stays
in rotation throughout and is the measured outcome.

### Three tiers

| Tier | Tests | Example (facial nerve branches) |
| --- | --- | --- |
| **Atoms** | One fact each | "Which branch supplies the frontalis?" |
| **Orchestrator** | Structure, order, relation, organising principle | "In what order do the branches run, superior to inferior?" |
| **Original** | Full composite recall — the target, retained in both arms | "Name the five branches of the facial nerve" |

This is **additive, not substitutive**: nothing is replaced, promoted, or restored. That
is both the pedagogically better-supported configuration (4C/ID prescribes whole-task and
part-task practice together) and by far the safer thing to build — it needs no scheduling
surgery.

## Design stance

Positions that shape everything below:

1. **Triage before decomposition.** A leech is a symptom with several possible causes
   (compound formulation, ambiguity, sibling interference, missing comprehension, genuine
   difficulty). Only some respond to splitting. Splitting an interference-driven leech
   makes it worse. Classify first, act second.
2. **Suspension is the default; decomposition is the exception.** Suspending is free,
   instant, and often the *correct* outcome — the Anki manual itself endorses dropping
   difficult, obscure items so time goes elsewhere. Decomposition is justified only when
   the content is worth knowing AND the formulation is broken. Expect that to be a
   minority of leeches. An add-on that says "not worth saving" for most cards and
   decomposes the rest is cheaper, more trustworthy, and more useful than one that
   decomposes everything.
3. **Suspend first, decompose lazily.** On leech detection, suspend immediately — stop the
   time bleed at zero cost. Decomposition runs out of band afterward; atoms enter only once
   generated and approved. Suspension and decomposition are sequential, not alternatives.
   The user is never worse off than the status quo if the LLM step fails or is rejected.
4. **Add, never replace.** The original card stays in rotation. Atoms and the orchestrator
   are added beneath it as scaffolding. This removes the entire promote-back state machine
   (the riskiest code in the project), keeps the original available as a clean outcome
   measure, and matches the instructional-design evidence, which supports part-task
   practice only *alongside* whole-task practice — never instead of it.
5. **The orchestrator must test assembly, not re-enumeration.** If its answer is the same
   set as the original's answer, it is a duplicate, and you have manufactured a sibling
   interference pair — the exact failure mode triage exists to catch. It should ask about
   *relations between* the atoms: order, organising principle, causal links, the exception.
   The generator must be allowed to return **no orchestrator** rather than invent a
   spurious one.
6. **Never block the reviewer.** All LLM work happens out of band. The review loop stays
   synchronous and instant.
7. **Instrument from day one.** The central claim is unvalidated in the literature, and
   the part-task research is ambivalent about decomposition *without* integration — which
   is precisely why the orchestrator matters. Build the measurement apparatus into the
   pipeline from the start; retrofitting makes all early data useless. See
   **[EXPERIMENT.md](EXPERIMENT.md)** for the randomised design, confound analysis, power
   calculations, and schema. This is the moat, not the LLM call.
8. **Watch time-on-task.** Treatment adds ~4 cards against a control that adds none, so it
   receives several times the study time. Raw recall will favour it for that reason alone.
   Report **efficiency** — recall per minute invested in the lineage — as the primary
   outcome.

### Bury is not a candidate

Burying returns a card the next day. It is a within-day sibling-collision tool, not a
leech remedy — it would re-present the broken card tomorrow and inflate review counts.
Suspend or nothing.

### The triage decision is two-axis

|                           | Formulation broken | Formulation fine                      |
| ------------------------- | ------------------ | ------------------------------------- |
| **Content worth knowing** | **Decompose**      | Rephrase / add context / learn outside Anki |
| **Content not worth it**  | Suspend            | Suspend or delete                     |

Only the top-left quadrant justifies API spend and 3x review load. The "worth knowing"
axis cannot come from the LLM alone — it depends on user context (board-exam deck vs.
casual language deck), so it needs **deck-level configuration** of the preferred default
action. Interference-driven leeches are fixed by suspending a *sibling*, not by splitting.

## Non-negotiable constraints

- **No destructive edits without consent.** Never delete, never replace. The original card
  is left in rotation untouched; the intervention only ever adds cards alongside it.
- **Sync-safe provenance.** State lives in note fields and tags so it survives sync to
  AnkiDroid/AnkiMobile. A local DB may cache, never own.
- **Entailment constraint.** Generated atoms must be strictly entailed by the source note.
  No new facts, no outside knowledge. This is a prompt constraint *and* a validation step.
- **Review budgets.** Hard caps on fan-out per card and new cards per day.
- **Bring your own key.** User supplies their own API key. No proxy in v1.

## Milestones

### M0 — Spike (1 week)
Prove the risky parts before building UI.

- Minimal add-on skeleton loading in current Anki (`aqt`, `addons21`).
- Read scheduling signals: `prop:lapses`, FSRS `card.memory_state` (stability,
  difficulty), `col.card_stats_data(card_id)`. Confirm what's reachable with FSRS on
  *and* off — you cannot assume FSRS.
- Hand-write **two** prompts — decomposition and orchestration — and run both over ~30 of
  your own real leeches. Read every output.

**Gate (two parts):** Do you judge the atoms genuinely useful on a clear majority? And can
the model produce a *non-redundant* orchestrator — one asking about relations rather than
restating the original? Orchestrator quality is the likely weak link: "find the organising
principle" is a harder generation problem than "split this list," and some cards have no
interesting structure at all. If orchestrators come back as reworded originals, that tier
needs rethinking before anything else gets built.

### M1 — Detection and triage (1–2 weeks)
- Candidate scorer combining lapse count, FSRS difficulty, total time spent, and
  again-rate. Time-cost matters more than raw lapses — a card failed 10 times in 4
  seconds each is cheaper than one failed 5 times at 30 seconds.
- LLM triage classifier returning three things:
  - **failure mode** — compound / ambiguous / interference / comprehension-gap / genuinely-hard
  - **estimated value** — how foundational vs. obscure the content is, biased by the
    deck's configured stakes level
  - **recommended action** — `suspend` / `decompose` / `rephrase` / `add-context` /
    `leave-alone` / `check-siblings`, plus confidence
- `suspend` is a first-class outcome and expected to be the most common one. Make it
  one-click-accept in bulk so clearing a leech backlog is fast and satisfying.
- Surface the *reason* in plain language ("bundles a 5-item list"). This teaches
  card-writing and reduces future leeches — a real benefit worth instrumenting.
- Browser sidebar view: candidates ranked by time cost, with triage labels. Read-only.

- Add the experiment sidecar schema and **start recording baselines now**, before any
  intervention exists. Free to do, and impossible to reconstruct later.

**Gate:** Triage labels agree with your own judgment on a held-out set of your leeches —
especially the suspend/decompose split, which is the decision that controls all downstream
cost. Feed your decomposable count into `power_analysis.py` to decide whether the RCT is
viable for your collection size.

### M2 — Generation with a human gate (2 weeks)
- Decomposition into N atoms (N configurable, default 3, allow 2–5 — forcing exactly 3
  is arbitrary and will produce padding).
- Preserve cloze syntax, media references, and note type compatibility.
- Validation pass: entailment check against source, duplicate detection against the
  existing collection (critical — you may be generating a card the user already has),
  and a confusability check between the new atoms.
- **Orchestrator generation** as a separate prompt and a separately rejectable proposal.
  Classify its kind (`sequence` / `principle` / `relation` / `exception`) so the analysis
  can later ask which kinds actually work.
- **Redundancy check between orchestrator and original.** If the orchestrator's answer is
  the same set as the original's, reject and regenerate. Without this the intervention
  creates sibling interference.
- **Diff review UI.** Original card shown as context (unchanged), proposed atoms and
  orchestrator alongside. Edit, accept individually, reject, regenerate. Nothing touches
  the collection without approval.
- Batch + cache calls. Show cost estimates before running.
- **Randomise at the gate**, logging the assignment *before* the user sees the proposal so
  intent-to-treat analysis stays possible. Control arm is simply "add nothing" — cheap to
  implement, but the assignment and baseline must still be recorded.

**Gate:** Generated atoms pass your review without edits ~70%+ of the time, and
orchestrators are non-redundant on a clear majority.

### M3 — Linking, budgets, logging (1 week)
Much smaller than originally scoped. Because the design is additive, there is no
suspend/unsuspend state machine, no graduation criteria, no promote-back logic, and no
scheduling rollback. That removed the riskiest code in the project.

- Link added cards to the original: lineage in the sidecar DB, mirrored into note fields
  and tags so it survives sync to AnkiDroid/AnkiMobile.
- Enforce fan-out caps and daily new-card budgets per deck.
- Log state changes for audit, and support "undo this intervention" = delete the added
  cards (the original was never modified, so nothing needs restoring).
- Track cumulative lineage study time for the efficiency outcome.

**Gate:** Run interventions on your own collection for several weeks. Verify lineage
survives a round-trip sync to a mobile client, and that the original card's scheduling is
provably untouched.

### M4 — Hardening for release (2 weeks)
- Daily budget enforcement and fan-out caps.
- Automatic collection backup before any batch operation.
- Undo integration via `CollectionOp` so Ctrl+Z works as users expect.
- Config UI: model/provider selection, thresholds, deck scoping, prompt overrides.
- Graceful degradation: no API key, no network, rate limits, malformed responses.
- Logging with enough detail to audit and reverse every change.

### M5 — Ship and learn (ongoing)
- AnkiWeb submission. Pick a license deliberately — Anki is AGPL-3.0 and most add-ons
  follow suit.
- Dogfood for a full month before promoting it anywhere.
- Instrument outcomes (locally, opt-in): do scaffolded cards actually outperform the
  originals they replaced? This is your real validation and nobody else has this data.

## Deferred

Don't build these until M3 is stable: multi-provider abstraction, local models, image
generation, mobile support, paid tier/hosted proxy, shared decks of decomposed cards,
automatic unattended operation with no review gate.

## Open questions worth resolving early

- **Interval inheritance.** Should atoms start at day 0, or inherit some stability from
  the parent? Day 0 is safe but floods the new-card queue. No established answer —
  prototype both.
- **Does the atom set stay coherent?** Three atoms reviewed independently may drift into
  testing overlapping things. Worth measuring.
- **Can an LLM reliably write a good orchestrator?** The biggest unknown in the design.
  Finding the organising principle is harder than splitting a list, and some cards have no
  interesting structure. Answer this in M0 before building on the assumption.
- **Which orchestrator kinds work?** Sequence, principle, relation, exception. Record the
  kind on every card so the analysis can tell you, rather than guessing now.
- **Does the original card improve, or just get crowded out?** Adding 4 cards to a deck
  increases total load. Watch for the original's performance improving while the *rest of
  the collection* degrades from the added burden — a cost the per-card analysis cannot see.
- **Second-order leeches.** What happens when a generated atom itself becomes a leech?
  Cap recursion depth; a leech atom probably signals bad triage upstream.
- **What fraction of leeches are actually decomposable?** Measure this in M0 on your own
  collection. If it's under ~15%, the product is really a triage tool with decomposition
  as a side feature — which changes the positioning, the pricing, and the build order.
- **Does decomposition beat suspension on net time?** The honest comparison isn't
  "did the user learn the fact" but "did learning it cost less than the time reclaimed by
  dropping it." Only long-run instrumentation answers this.

## Prior art to study before writing code

- `thiswillbeyourgithub/AnkiAIUtils` — closest in spirit; author wants packaging help,
  possible collaboration rather than competition.
- `iamjustkoi/LeechToolkit` — leech lifecycle, including reverting leech status.
- `Arthur-Milchior/anki-trigger-action-on-note` — maturity-gated card visibility. This is
  your gating primitive, already built.
- `gustavotrott/anki-suspend-siblings-until-mature` — same, narrower.
- `TheLycoi/anki-bury-explain` — same trigger, stops at advice.
- `djt97/anki-skill` — cost-based card health metric worth borrowing.
- `zarnthyr/card-janitor` — policy-based lifecycle actions.

## References

- [Anki add-on docs](https://addon-docs.ankiweb.net/) — hooks, filters, the `anki` module
- [Anki manual: leeches](https://docs.ankiweb.net/leeches.html) — default is 8 lapses →
  tag + suspend, retriggering at half-threshold intervals; also endorses selectively
  deleting difficult/obscure items
- [Dealing with leech cards (RemNote)](https://help.remnote.com/en/articles/7183408-dealing-with-leech-cards)
  — the hardest 5–10% of cards can consume ~50% of study time
- [Managing forgetting](https://wisc.pb.unizin.org/lctlresources/chapter/anki-part-ii-how-to-manage-forgetting/)
  — 500 leeches in a 10k collection can eat 25–50% of review time
- [Treating leeches](https://www.polyglossic.com/anki-leeches-strategies/) — the periodic
  leech-review-session workflow your batch UI should mirror
- [Twenty rules of formulating knowledge](https://www.supermemo.com/en/blog/twenty-rules-of-formulating-knowledge)
  — the minimum information principle
- [FSRS](https://github.com/open-spaced-repetition/fsrs4anki) — difficulty/stability/retrievability model

### Evidence for the three-tier structure

- [Blueprints for complex learning: the 4C/ID model](https://www.researchgate.net/publication/225798787_Blueprints_for_complex_learning_The_4CID-model)
  — van Merriënboer; whole learning tasks and part-task practice as distinct, co-present
  components. The orchestrator is the whole-task tier.
- [Training concurrent multistep procedural tasks](https://pubmed.ncbi.nlm.nih.gov/11132799/)
  — with total training trials equated, part-task practice *including integration* matched
  whole-task training and beat pure part-task training.
- [Part-task training meta-analysis](https://www.researchgate.net/publication/236926003_Effectiveness_of_Part-Task_Training_and_Increasing-Difficulty_Training_Strategies_A_Meta-Analysis_Approach)
  — part-task training succeeds when integration of the parts is varied in priority.
- [Lim, Reiser & Olina](https://knilt.arcc.albany.edu/images/6/6a/Lim_etal_ETR&D_2009.pdf)
  — the counter-evidence: whole-task beat *pure* part-task on acquisition and transfer.
  The reason atoms alone is the weaker hypothesis.
- [Element interactivity and task complexity](https://files.eric.ed.gov/fulltext/EJ1407814.pdf)
  — cognitive load theory's account of when splitting should help at all.

Content from external sources was rephrased for compliance with licensing restrictions.
