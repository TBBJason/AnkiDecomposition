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
Build a synthetic collection.anki2 for testing extract_candidates.py without
touching a real collection. Mirrors Anki's modern schema closely enough to
exercise every code path: FSRS and non-FSRS cards, cloze notes, media refs,
suspended cards, and a range of time costs.
"""

import json
import os
import random
import sqlite3
import sys
import time

FIELD_SEP = "\x1f"


def build(path, schema="modern"):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    c = con.cursor()

    c.executescript("""
        CREATE TABLE col (
            id integer PRIMARY KEY, crt integer NOT NULL, mod integer NOT NULL,
            scm integer NOT NULL, ver integer NOT NULL, dty integer NOT NULL,
            usn integer NOT NULL, ls integer NOT NULL, conf text NOT NULL,
            models text NOT NULL, decks text NOT NULL, dconf text NOT NULL,
            tags text NOT NULL
        );
        CREATE TABLE notes (
            id integer PRIMARY KEY, guid text NOT NULL, mid integer NOT NULL,
            mod integer NOT NULL, usn integer NOT NULL, tags text NOT NULL,
            flds text NOT NULL, sfld integer NOT NULL, csum integer NOT NULL,
            flags integer NOT NULL, data text NOT NULL
        );
        CREATE TABLE cards (
            id integer PRIMARY KEY, nid integer NOT NULL, did integer NOT NULL,
            ord integer NOT NULL, mod integer NOT NULL, usn integer NOT NULL,
            type integer NOT NULL, queue integer NOT NULL, due integer NOT NULL,
            ivl integer NOT NULL, factor integer NOT NULL, reps integer NOT NULL,
            lapses integer NOT NULL, left integer NOT NULL, odue integer NOT NULL,
            odid integer NOT NULL, flags integer NOT NULL, data text NOT NULL
        );
        CREATE TABLE revlog (
            id integer PRIMARY KEY, cid integer NOT NULL, usn integer NOT NULL,
            ease integer NOT NULL, ivl integer NOT NULL, lastIvl integer NOT NULL,
            factor integer NOT NULL, time integer NOT NULL, type integer NOT NULL
        );
    """)

    if schema == "modern":
        c.executescript("""
            CREATE TABLE decks (
                id integer PRIMARY KEY, name text NOT NULL, mtime_secs integer NOT NULL,
                usn integer NOT NULL, common blob NOT NULL, kind blob NOT NULL
            );
            CREATE TABLE notetypes (
                id integer PRIMARY KEY, name text NOT NULL, mtime_secs integer NOT NULL,
                usn integer NOT NULL, config blob NOT NULL
            );
            CREATE TABLE fields (
                ntid integer NOT NULL, ord integer NOT NULL, name text NOT NULL,
                config blob NOT NULL, PRIMARY KEY (ntid, ord)
            );
        """)

    now = int(time.time())

    # ---- note types -----------------------------------------------------
    BASIC, CLOZE = 1000, 2000
    models = {
        str(BASIC): {"id": BASIC, "name": "Basic", "flds": [
            {"name": "Front", "ord": 0}, {"name": "Back", "ord": 1}]},
        str(CLOZE): {"id": CLOZE, "name": "Cloze", "flds": [
            {"name": "Text", "ord": 0}, {"name": "Extra", "ord": 1}]},
    }
    decks = {
        "1": {"id": 1, "name": "Default"},
        "1700000000001": {"id": 1700000000001, "name": "Pharmacology"},
        "1700000000002": {"id": 1700000000002, "name": "Spanish::Vocab"},
    }

    c.execute(
        "INSERT INTO col VALUES (1,?,?,?,18,0,0,0,?,?,?,?,?)",
        (now - 86400 * 400, now, now, "{}", json.dumps(models),
         json.dumps(decks), "{}", "{}"),
    )

    if schema == "modern":
        for ntid, model in ((BASIC, "Basic"), (CLOZE, "Cloze")):
            c.execute("INSERT INTO notetypes VALUES (?,?,?,0,?)",
                      (ntid, model, now, b""))
        for ntid, names in ((BASIC, ["Front", "Back"]), (CLOZE, ["Text", "Extra"])):
            for ord_, name in enumerate(names):
                c.execute("INSERT INTO fields VALUES (?,?,?,?)",
                          (ntid, ord_, name, b""))
        # Modern schema separates deck name components with \x1f
        for did, name in ((1, "Default"),
                          (1700000000001, "Pharmacology"),
                          (1700000000002, "Spanish\x1fVocab")):
            c.execute("INSERT INTO decks VALUES (?,?,?,0,?,?)",
                      (did, name, now, b"", b""))

    # ---- test notes: deliberately varied ---------------------------------
    specs = [
        # (mid, fields, tags, lapses, reps, avg_ms, fsrs?, suspended?, note)
        (BASIC, ["Name the <b>five</b> branches of the facial nerve",
                 "<ul><li>Temporal</li><li>Zygomatic</li><li>Buccal</li>"
                 "<li>Marginal mandibular</li><li>Cervical</li></ul>"],
         "leech anatomy", 11, 28, 34000, True, True,
         "compound list - prime decomposition candidate, very expensive"),

        (BASIC, ["Adverse effects of amiodarone",
                 "Pulmonary fibrosis, hepatotoxicity, thyroid dysfunction, "
                 "corneal deposits, blue-grey skin, bradycardia"],
         "leech pharm", 9, 24, 41000, True, True,
         "compound list, high cost"),

        (BASIC, ["What is the capital of Australia?", "Canberra"],
         "geography", 4, 19, 4200, True, False,
         "atomic already - splitting would not help"),

        (CLOZE, ["The {{c1::glossopharyngeal}} nerve is cranial nerve "
                 "{{c2::IX}}", "[image]"],
         "leech anatomy", 8, 22, 12000, True, True,
         "cloze, possible sibling interference"),

        (BASIC, ["estar", "to be (temporary states, locations)"],
         "leech spanish", 10, 31, 8000, True, False,
         "classic interference with 'ser' - splitting makes it WORSE"),

        (BASIC, ["ser", "to be (permanent traits, identity)"],
         "leech spanish", 12, 35, 9000, True, False,
         "the interfering sibling of the card above"),

        (BASIC, ["Obscure 1954 ICD code for unspecified gastritis", "K29.70"],
         "leech trivia", 7, 15, 6000, True, True,
         "low value - correct action is suspend/delete, not decompose"),

        (BASIC, ["Mechanism of action of metformin",
                 "Activates AMPK, decreases hepatic gluconeogenesis, "
                 "increases peripheral insulin sensitivity"],
         "pharm", 5, 18, 22000, False, False,
         "no FSRS data - exercises the SM-2 fallback path"),

        (BASIC, ["Define homeostasis", "Maintenance of a stable internal "
                 "environment despite external change"],
         "", 1, 12, 3000, True, False,
         "below default lapse threshold - should be filtered out"),

        (BASIC, ["Steps of the clotting cascade (intrinsic pathway)",
                 "XII to XIIa, XI to XIa, IX to IXa, VIII cofactor, "
                 "X to Xa, prothrombin to thrombin"],
         "leech physio", 14, 40, 52000, True, True,
         "worst offender - should rank #1 by cost"),
    ]

    rng = random.Random(42)
    nid_base = 1600000000000
    cid_base = 1600000000000
    rev_id = (now - 86400 * 300) * 1000

    for i, (mid, fields, tags, lapses, reps, avg_ms, fsrs, susp, _note) in enumerate(specs):
        nid = nid_base + i * 1000
        cid = cid_base + i * 1000
        did = (1700000000001 if "pharm" in tags or "anatomy" in tags or "physio" in tags
               else 1700000000002 if "spanish" in tags else 1)
        flds = FIELD_SEP.join(fields)
        tag_str = " {} ".format(tags.strip()) if tags.strip() else ""

        c.execute("INSERT INTO notes VALUES (?,?,?,?,0,?,?,?,0,0,'')",
                  (nid, "guid%d" % i, mid, now, tag_str, flds, fields[0][:50]))

        data = ""
        if fsrs:
            # FSRS internal difficulty is 1-10; stability in days.
            d = round(rng.uniform(7.5, 9.9), 2) if lapses >= 8 else round(rng.uniform(4.0, 7.0), 2)
            s = round(rng.uniform(1.5, 12.0), 2) if lapses >= 8 else round(rng.uniform(15.0, 90.0), 2)
            data = json.dumps({"s": s, "d": d, "dr": 0.9})

        c.execute(
            "INSERT INTO cards VALUES (?,?,?,0,?,0,2,?,?,?,?,?,?,0,0,0,0,?)",
            (cid, nid, did, now, -1 if susp else 2, 500,
             rng.randint(1, 30), 1900 + rng.randint(-400, 600), reps, lapses, data),
        )

        # Review log: realistic spread, with lapses recorded as ease=1.
        for j in range(reps):
            rev_id += rng.randint(60_000, 86_400_000)
            is_lapse = j < lapses
            c.execute(
                "INSERT INTO revlog VALUES (?,?,0,?,?,?,?,?,?)",
                (rev_id, cid, 1 if is_lapse else rng.randint(2, 4),
                 rng.randint(1, 40), rng.randint(1, 20), 2000,
                 int(avg_ms * rng.uniform(0.7, 1.3)), 1 if j else 0),
            )

        # One manual/rescheduled entry (type=4) that must NOT count as study time.
        rev_id += 1000
        c.execute("INSERT INTO revlog VALUES (?,?,0,0,0,0,0,?,4)",
                  (rev_id, cid, 999_999_999))

    con.commit()
    con.close()
    print("built {} ({} schema, {} cards)".format(path, schema, len(specs)))


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "test_collection.anki2"
    schema = sys.argv[2] if len(sys.argv) > 2 else "modern"
    build(out, schema)
