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
Extract struggling-card candidates from an Anki collection, ranked by time cost.

READ-ONLY. Opens the database in SQLite read-only mode and never writes to it.
Still: run it against a COPY, not your live collection. See README.md.

Outputs:
  candidates.csv    human-readable, ranked, open in any spreadsheet
  candidates.jsonl  one card per line, ready to feed to an LLM for triage
  summary printed to stdout
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict

FIELD_SEP = "\x1f"


# ---------------------------------------------------------------- helpers

def strip_html(text):
    """Reduce Anki field HTML to plain text for LLM consumption."""
    if not text:
        return ""
    # Cloze markers carry meaning for triage - keep them visible.
    text = re.sub(r"\{\{c(\d+)::(.*?)(::.*?)?\}\}", r"[cloze\1: \2]", text, flags=re.S)
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"</(div|p|li|tr|h[1-6])>", " ", text, flags=re.I)
    text = re.sub(r"<li[^>]*>", " - ", text, flags=re.I)
    text = re.sub(r"\[sound:[^\]]*\]", " [audio] ", text)
    text = re.sub(r"<img[^>]*>", " [image] ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
    return re.sub(r"\s+", " ", text).strip()


def connect_readonly(path):
    uri = "file:{}?mode=ro".format(path.replace("?", "%3f").replace("#", "%23"))
    return sqlite3.connect(uri, uri=True)


def table_exists(con, name):
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def load_deck_names(con):
    """Newer Anki keeps decks in their own table; older versions use col.decks JSON."""
    names = {}
    if table_exists(con, "decks"):
        try:
            for did, name in con.execute("SELECT id, name FROM decks"):
                # Newer schema uses \x1f to separate deck name components.
                names[did] = (name or "").replace("\x1f", "::")
            if names:
                return names
        except sqlite3.Error:
            pass
    try:
        raw = con.execute("SELECT decks FROM col").fetchone()
        if raw and raw[0]:
            for did, deck in json.loads(raw[0]).items():
                names[int(did)] = deck.get("name", "")
    except (sqlite3.Error, ValueError, TypeError):
        pass
    return names


def load_field_names(con):
    """Map notetype id -> ordered list of field names."""
    fields = defaultdict(dict)
    if table_exists(con, "fields"):
        try:
            for ntid, ord_, name in con.execute(
                "SELECT ntid, ord, name FROM fields"
            ):
                fields[ntid][ord_] = name
            if fields:
                return {k: [v[i] for i in sorted(v)] for k, v in fields.items()}
        except sqlite3.Error:
            pass
    try:
        raw = con.execute("SELECT models FROM col").fetchone()
        if raw and raw[0]:
            out = {}
            for mid, model in json.loads(raw[0]).items():
                flds = sorted(model.get("flds", []), key=lambda f: f.get("ord", 0))
                out[int(mid)] = [f.get("name", "") for f in flds]
            return out
    except (sqlite3.Error, ValueError, TypeError):
        pass
    return {}


def parse_fsrs(data_str):
    """
    Pull FSRS memory state out of the cards.data column.

    Anki stores something like {"s": 12.3, "d": 5.6, "dr": 0.9}. The `d` here is
    FSRS's internal 1-10 difficulty; the Browse column and `prop:d` show it
    normalised to 0-1 as (d-1)/9. We report both and do not guess which you want.
    Returns (stability, difficulty_raw, difficulty_normalised).
    """
    if not data_str:
        return (None, None, None)
    try:
        data = json.loads(data_str)
    except (ValueError, TypeError):
        return (None, None, None)
    if not isinstance(data, dict):
        return (None, None, None)
    s = data.get("s")
    d = data.get("d")
    d_norm = None
    if isinstance(d, (int, float)):
        if 1.0 <= d <= 10.0:
            d_norm = round((d - 1.0) / 9.0, 4)
        elif 0.0 <= d <= 1.0:   # already normalised in some versions
            d_norm = round(float(d), 4)
    return (
        round(float(s), 3) if isinstance(s, (int, float)) else None,
        round(float(d), 3) if isinstance(d, (int, float)) else None,
        d_norm,
    )


def cost_score(total_time_s, lapses, reps):
    """
    Transparent, tunable heuristic. Primary term is literal minutes spent;
    the lapse-rate multiplier promotes cards that are *still* failing over
    cards that were expensive once and then stuck.

    This is a starting point to calibrate in M0, not a validated metric.
    """
    minutes = total_time_s / 60.0
    lapse_rate = lapses / float(reps) if reps else 0.0
    return round(minutes * (1.0 + 2.0 * lapse_rate), 3)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Rank struggling Anki cards by time cost (read-only)."
    )
    ap.add_argument("collection", help="path to a COPY of collection.anki2")
    ap.add_argument("--min-lapses", type=int, default=3,
                    help="minimum lapses to be a candidate (default 3)")
    ap.add_argument("--limit", type=int, default=200,
                    help="max candidates to export (default 200)")
    ap.add_argument("--outdir", default=".", help="output directory")
    ap.add_argument("--include-suspended", action="store_true",
                    help="include suspended cards (default: include them, since "
                         "Anki suspends leeches automatically)")
    ap.add_argument("--exclude-suspended", action="store_true",
                    help="exclude suspended cards")
    args = ap.parse_args()

    if not os.path.exists(args.collection):
        sys.exit("error: no such file: {}".format(args.collection))

    con = connect_readonly(args.collection)

    deck_names = load_deck_names(con)
    field_names = load_field_names(con)

    # Per-card review aggregates. revlog.time is milliseconds per answer.
    # type=0 learn, 1 review, 2 relearn, 3 filtered/cram, 4 manual/rescheduled.
    # Manual entries are excluded: they are not real study time.
    agg = {}
    for cid, total_ms, n_rev, n_again in con.execute(
        """
        SELECT cid,
               SUM(time)                        AS total_ms,
               COUNT(*)                         AS n_rev,
               SUM(CASE WHEN ease = 1 THEN 1 ELSE 0 END) AS n_again
        FROM revlog
        WHERE type != 4
        GROUP BY cid
        """
    ):
        agg[cid] = (total_ms or 0, n_rev or 0, n_again or 0)

    suspended_clause = ""
    if args.exclude_suspended:
        suspended_clause = "AND c.queue != -1"

    rows = []
    query = """
        SELECT c.id, c.nid, c.did, c.ord, c.reps, c.lapses, c.ivl,
               c.factor, c.queue, c.type, c.data,
               n.mid, n.flds, n.tags
        FROM cards c
        JOIN notes n ON n.id = c.nid
        WHERE c.lapses >= ?
        {}
    """.format(suspended_clause)

    for r in con.execute(query, (args.min_lapses,)):
        (cid, nid, did, ord_, reps, lapses, ivl,
         factor, queue, ctype, data, mid, flds, tags) = r

        total_ms, n_rev, n_again = agg.get(cid, (0, 0, 0))
        total_s = total_ms / 1000.0

        stability, d_raw, d_norm = parse_fsrs(data)

        values = (flds or "").split(FIELD_SEP)
        names = field_names.get(mid, [])
        pairs = []
        for i, val in enumerate(values):
            plain = strip_html(val)
            if not plain:
                continue
            label = names[i] if i < len(names) else "Field{}".format(i + 1)
            pairs.append((label, plain))

        rows.append({
            "card_id": cid,
            "note_id": nid,
            "deck": deck_names.get(did, "(unknown)"),
            "template_ord": ord_,
            "lapses": lapses,
            "reviews": reps,
            "lapse_rate": round(lapses / float(reps), 3) if reps else None,
            "again_count": n_again,
            "total_time_min": round(total_s / 60.0, 2),
            "avg_time_s": round(total_s / n_rev, 1) if n_rev else None,
            "interval_days": ivl,
            "ease_factor": round(factor / 1000.0, 2) if factor else None,
            "fsrs_stability": stability,
            "fsrs_difficulty_raw": d_raw,
            "fsrs_difficulty_0_1": d_norm,
            "suspended": queue == -1,
            "tagged_leech": "leech" in (tags or "").lower(),
            "tags": (tags or "").strip(),
            "cost_score": cost_score(total_s, lapses, reps),
            "fields": pairs,
        })

    con.close()

    rows.sort(key=lambda x: x["cost_score"], reverse=True)
    selected = rows[:args.limit]

    if not os.path.isdir(args.outdir):
        os.makedirs(args.outdir)
    csv_path = os.path.join(args.outdir, "candidates.csv")
    jsonl_path = os.path.join(args.outdir, "candidates.jsonl")

    csv_cols = [
        "cost_score", "total_time_min", "lapses", "reviews", "lapse_rate",
        "again_count", "avg_time_s", "fsrs_difficulty_0_1", "fsrs_stability",
        "interval_days", "suspended", "tagged_leech", "deck", "card_id",
        "card_text",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=csv_cols, extrasaction="ignore")
        w.writeheader()
        for row in selected:
            out = dict(row)
            out["card_text"] = " | ".join(
                "{}: {}".format(k, v) for k, v in row["fields"]
            )[:400]
            w.writerow(out)

    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for row in selected:
            fh.write(json.dumps({
                "card_id": row["card_id"],
                "deck": row["deck"],
                "fields": [{"name": k, "value": v} for k, v in row["fields"]],
                "stats": {
                    "lapses": row["lapses"],
                    "reviews": row["reviews"],
                    "lapse_rate": row["lapse_rate"],
                    "again_count": row["again_count"],
                    "total_time_min": row["total_time_min"],
                    "avg_time_s": row["avg_time_s"],
                    "fsrs_difficulty_0_1": row["fsrs_difficulty_0_1"],
                    "fsrs_stability": row["fsrs_stability"],
                    "interval_days": row["interval_days"],
                },
                "tags": row["tags"],
            }, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------ summary
    total_cards = len(rows)
    has_fsrs = sum(1 for r in rows if r["fsrs_difficulty_0_1"] is not None)
    total_hours = sum(r["total_time_min"] for r in rows) / 60.0
    tagged = sum(1 for r in rows if r["tagged_leech"])

    print("")
    print("  Candidates (lapses >= {}): {}".format(args.min_lapses, total_cards))
    print("  Tagged 'leech' by Anki:    {}".format(tagged))
    print("  With FSRS memory state:    {}{}".format(
        has_fsrs, "   (FSRS appears OFF - difficulty unavailable)"
        if has_fsrs == 0 else ""))
    print("  Total time sunk into them: {:.1f} hours".format(total_hours))
    if total_cards:
        print("  Worst card alone:          {:.1f} min".format(
            max(r["total_time_min"] for r in rows)))
    print("")
    print("  Exported top {} to:".format(len(selected)))
    print("    {}".format(csv_path))
    print("    {}".format(jsonl_path))
    print("")
    print("  Next: read candidates.csv top to bottom and label each card yourself")
    print("  using triage_prompt.md. Your own labels are the ground truth you will")
    print("  measure the LLM against.")
    print("")


if __name__ == "__main__":
    main()
