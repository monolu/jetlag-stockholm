"""
Builds questions.json: the whole investigation book, all six categories.

Source is the community card spreadsheet, one tab per category, exported to
source/questions/*.csv. The tabs list subjects in blank-line separated groups;
the group names come from the rulebook.

Run: python build_questions.py
"""

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source", "questions")

SHEET = ("https://docs.google.com/spreadsheets/d/"
         "1ZigDKsSCDxbp0JDWTnt0OGOlfxNEqICA3FnXy46p1Jk")

ALL_SIZES = ["small", "medium", "large"]
SIZE_HEADINGS = {
    "all games": ALL_SIZES,
    "medium & large": ["medium", "large"],
    "medium & up": ["medium", "large"],
    "large games only": ["large"],
    "large only": ["large"],
}

# The sheet separates these with blank rows but doesn't name the groups.
GROUPS = {
    "matching": ["Transit", "Administrative divisions", "Natural",
                 "Places of interest", "Public utilities"],
    "measuring": ["Transit", "Borders", "Natural",
                  "Places of interest", "Public utilities"],
}

CATEGORIES = [
    ("matching", "Matching", {"draw": 3, "keep": 1}, dict.fromkeys(ALL_SIZES, 5)),
    ("measuring", "Measuring", {"draw": 3, "keep": 1}, dict.fromkeys(ALL_SIZES, 5)),
    ("thermometer", "Thermometer", {"draw": 2, "keep": 1}, dict.fromkeys(ALL_SIZES, 5)),
    ("radar", "Radar", {"draw": 2, "keep": 1}, dict.fromkeys(ALL_SIZES, 5)),
    ("photo", "Photo", {"draw": 1, "keep": 1}, {"small": 10, "medium": 10, "large": 20}),
    ("tentacles", "Tentacles", {"draw": 4, "keep": 2}, dict.fromkeys(ALL_SIZES, 5)),
]

DISTANCE = re.compile(r"^([\d.]+)\s*mi\s*([\d.]+)\s*(km|m)$", re.I)

# The metric rulebook is not a conversion of the imperial one: it prints its own
# round numbers. These are what we play, keyed by the mile figure on the same card.
METRIC = {
    "thermometer": {0.5: 1000, 3: 5000, 10: 15000, 50: 75000},
    "radar": {0.25: 500, 0.5: 1000, 1: 2000, 3: 5000, 5: 10000, 10: 15000,
              25: 40000, 50: 80000, 100: 160000},
    "tentacles": {1: 2000, 15: 25000},
}


def metres_label(metres):
    return f"{metres} m" if metres < 1000 else f"{metres // 1000} km"


def tidy(text):
    return " ".join((text or "").split())


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", tidy(text).lower()).strip("-")


def read(name):
    with open(os.path.join(SOURCE, name + ".csv"), encoding="utf-8") as fh:
        return [row + [""] * (4 - len(row)) for row in csv.reader(fh)]


def distance(text):
    """'0.25mi 402m' -> {miles, metres}. The tabs write both units in one cell."""
    match = DISTANCE.match(tidy(text).replace(" ", ""))
    if not match:
        return None
    metres = float(match.group(2)) * (1000 if match.group(3).lower() == "km" else 1)
    return {"miles": float(match.group(1)), "metres": int(round(metres))}


def header(rows):
    """The prompt sentence at the top of every tab."""
    for row in rows:
        if tidy(row[0]).rstrip(":").lower() == "question":
            # the tentacles tab is three columns wide, so the prompt is not always in row[1]
            return next((tidy(cell) for cell in row[1:] if tidy(cell)), None)
    return None


def body(rows):
    """Rows after the header block, dropping the column titles."""
    start = 0
    for i, row in enumerate(rows):
        if tidy(row[0]).rstrip(":").lower() == "question":
            start = i + 1
            break
    out = []
    for row in rows[start:]:
        first = tidy(row[0])
        if first.startswith("[") or first in ("", "Notes"):
            out.append(("blank", row) if not first else ("skip", row))
            continue
        out.append(("row", row))
    return out


def subjects(cid, rows):
    """Matching and measuring: a flat list broken into groups by blank rows."""
    names = GROUPS[cid]
    group, out = 0, []
    for kind, row in rows:
        if kind == "blank":
            if out:
                group += 1
            continue
        if kind == "skip":
            continue
        out.append({
            "id": f"{cid}-{slug(row[0])}",
            "subject": tidy(row[0]),
            "group": names[min(group, len(names) - 1)],
            "sizes": ALL_SIZES,
        })
    return out


def gated(cid, rows, value_key):
    """Thermometer, radar, tentacles, photo: size headings gate what is available."""
    sizes, out = ALL_SIZES, []
    for kind, row in rows:
        if kind != "row":
            continue
        label = tidy(row[0])
        if label.lower() in SIZE_HEADINGS:
            sizes = SIZE_HEADINGS[label.lower()]
            continue
        entry = {"id": f"{cid}-{slug(label)}", "subject": label, "sizes": sizes}
        if value_key == "distance":
            dist = distance(label)
            if dist:
                dist["metres"] = METRIC[cid].get(dist["miles"], dist["metres"])
                entry["subject"] = metres_label(dist["metres"])
                entry["id"] = f"{cid}-{slug(entry['subject'])}"
                entry["distance"] = dist
        elif value_key == "places":
            dist = distance(row[1])
            if dist:
                dist["metres"] = METRIC[cid].get(dist["miles"], dist["metres"])
                entry["distance"] = dist
        elif value_key == "requirements":
            if tidy(row[1]):
                entry["requirements"] = tidy(row[1])
        out.append(entry)
    return out


def build():
    categories = []
    for cid, name, cost, minutes in CATEGORIES:
        rows = read(cid)
        parsed = body(rows)
        if cid in GROUPS:
            questions = subjects(cid, parsed)
        elif cid in ("thermometer", "radar"):
            questions = gated(cid, parsed, "distance")
        elif cid == "tentacles":
            questions = gated(cid, parsed, "places")
        else:
            questions = gated(cid, parsed, "requirements")
        categories.append({
            "id": cid,
            "name": name,
            "cost": cost,
            "answer_minutes": minutes,
            "prompt": header(rows),
            "count": len(questions),
            "questions": questions,
        })
    return categories


if __name__ == "__main__":
    categories = build()
    doc = {
        "description": ("Every question in the Hide and Seek investigation book, by "
                        "category. `sizes` says which game sizes a question is available "
                        "in; we play medium. Distances carry the metric rulebook's own "
                        "figures, which are round numbers rather than conversions of the "
                        "mile ones."),
        "source": SHEET,
        "totals": {c["id"]: c["count"] for c in categories},
        "categories": categories,
    }
    doc["totals"]["all"] = sum(c["count"] for c in categories)

    with open(os.path.join(HERE, "questions.json"), "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)

    for c in categories:
        medium = sum(1 for q in c["questions"] if "medium" in q["sizes"])
        print(f"  {c['name']:12s} {c['count']:3d} questions  ({medium} in a medium game)"
              f"   draw {c['cost']['draw']}, keep {c['cost']['keep']}")
    print(f"\nwrote questions.json: {doc['totals']['all']} questions")
