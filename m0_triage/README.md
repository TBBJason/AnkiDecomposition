# M0: measure before you build

This answers one question: **what fraction of your struggling cards would actually
benefit from being split up?** That number decides whether the full project is worth
building. Nothing here is an Anki add-on — it is deliberately a throwaway measuring
instrument.

## Safety

The extractor opens SQLite in read-only mode and never writes to your collection. Even
so, **work on a copy.** Close Anki first so the database is not mid-write.

```bash
# macOS
cp ~/Library/Application\ Support/Anki2/User\ 1/collection.anki2 /tmp/col-copy.anki2
# Linux
cp ~/.local/share/Anki2/User\ 1/collection.anki2 /tmp/col-copy.anki2
# Windows (PowerShell)
copy "$env:APPDATA\Anki2\User 1\collection.anki2" "$env:TEMP\col-copy.anki2"
```

Find the exact path via Anki: **Tools → Add-ons → View Files**, then go up one level.
If your profile is not "User 1", adjust.

## Run

```bash
python3 extract_candidates.py /tmp/col-copy.anki2 --outdir out
```

Needs only Python 3 standard library. Options:

| Flag | Default | Meaning |
| --- | --- | --- |
| `--min-lapses N` | 3 | Minimum lapses to count as a candidate. Anki's own leech threshold is 8; 3 catches cards on the way to becoming leeches. |
| `--limit N` | 200 | How many top-cost cards to export. |
| `--exclude-suspended` | off | Skip suspended cards. Usually leave off — Anki auto-suspends leeches, so excluding them hides your worst offenders. |
| `--outdir DIR` | `.` | Where to write output. |

## Output

- **`candidates.csv`** — ranked, opens in any spreadsheet. Read this one.
- **`candidates.jsonl`** — one card per line with stats and cleaned text, ready to paste
  into an LLM alongside `triage_prompt.md`.

Columns worth understanding:

| Column | Why it matters |
| --- | --- |
| `cost_score` | Ranking heuristic: minutes spent, multiplied up by how often you still fail it. Transparent and tunable — see `cost_score()` in the script. |
| `total_time_min` | Literal minutes of your life spent on this one card, summed from Anki's review log. The most honest number here. |
| `lapse_rate` | lapses ÷ reviews. Catches cards that fail *proportionally* often, not just cards that are old. |
| `avg_time_s` | Seconds per review. High values usually mean an overloaded card — a strong decomposition signal. |
| `fsrs_difficulty_0_1` | FSRS's own verdict, normalised to match the `prop:d` search and the Browse column. Empty if FSRS is off. |
| `fsrs_stability` | Days until recall decays to 90%. Low stability + many reviews = not sticking. |

### Why rank by time rather than lapses

A card failed 10× at 3s each costs 30 seconds. One failed 5× at 40s each costs 200
seconds — nearly 7× more expensive with *half* the lapses. Ranking by lapse count gets
this backwards, which is why `prop:lapses` alone is a poor triage tool.

### If `fsrs_difficulty_0_1` is empty everywhere

FSRS is off. Enable it in **Deck Options → FSRS** (Anki 23.10+) and let it run a few
weeks, or proceed using `total_time_min`, `lapse_rate`, and `ease_factor`. The pipeline
must not assume FSRS is available — plenty of collections still use SM-2.

## Then

Follow the procedure at the bottom of `triage_prompt.md`: hand-label your top 40 first,
then compare against the LLM. Your labels are the ground truth.

## Quick alternative, no code

In Anki's Browse window, these get you a rough picture in ten minutes:

```
tag:leech                        everything Anki has flagged
prop:lapses>4                    struggling but not yet flagged
prop:lapses>4 prop:d>0.8         struggling and algorithmically hard (FSRS only)
prop:d>0.9 prop:s<21             hard and still not sticking (FSRS only)
tag:leech -is:suspended          leeches you unsuspended and are still fighting
```

Right-click the column headers to add **Difficulty**, **Stability**, **Lapses**, and
**Reviews**, then sort. Searches confirmed against the
[Anki manual](https://docs.ankiweb.net/searching.html); `prop:d`/`prop:s`/`prop:r`
require Anki 23.10+ with FSRS enabled.

## Testing without a real collection

```bash
python3 make_test_collection.py test_collection.anki2 modern
python3 extract_candidates.py test_collection.anki2 --outdir out
```

Generates a synthetic collection covering the cases that matter: compound lists, an
interference pair (`ser`/`estar`), cloze notes, media references, a low-value trivia card,
a card with no FSRS data, and one card below the lapse threshold that should be filtered
out. Pass `legacy` instead of `modern` to exercise the older `col.models`/`col.decks`
JSON schema path.
