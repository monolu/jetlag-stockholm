"""
Builds cards.json: every card in the Hide and Seek base game and Expansion Pack
Volume 1, as structured data.

Curse text comes from source/curses.csv, exported from the community card
spreadsheet. Card counts are checked against source/composition.csv from the same
sheet. Time bonus and powerup wording is transcribed from the physical cards.

Run: python build_cards.py
"""

import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source")

SHEET = ("https://docs.google.com/spreadsheets/d/"
         "1ZigDKsSCDxbp0JDWTnt0OGOlfxNEqICA3FnXy46p1Jk")

# [S30, M45, L60] and [S0.5, M1, L3] both appear in card text
SIZES = re.compile(r"\[\s*S\s*([\d.]+)\s*,\s*M\s*([\d.]+)\s*,\s*L\s*([\d.]+)\s*\]")


def number(text):
    value = float(text)
    return int(value) if value == int(value) else value


def slug(name):
    key = name.lower().replace("&", "and")
    key = key.replace("'", "").replace(chr(8217), "")
    key = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
    return re.sub(r"^curse-of-(the-)?", "curse-", key)


def read_sizes(*fields):
    """Every [S, M, L] triple in a card's text, in order of appearance."""
    out = []
    for field in fields:
        for match in SIZES.finditer(field or ""):
            out.append({"small": number(match.group(1)),
                        "medium": number(match.group(2)),
                        "large": number(match.group(3))})
    return out


def for_size(text, size):
    """The card as read at one game size, with the triples resolved."""
    index = {"small": 1, "medium": 2, "large": 3}[size]
    return SIZES.sub(lambda m: str(number(m.group(index))), text or "")


# ---------------------------------------------------------------- time bonuses

TIME_BONUSES = [
    ("red", "base", 25, {"small": 2, "medium": 3, "large": 5}),
    ("orange", "base", 15, {"small": 4, "medium": 6, "large": 10}),
    ("yellow", "base", 10, {"small": 6, "medium": 9, "large": 15}),
    ("green", "base", 3, {"small": 8, "medium": 12, "large": 20}),
    ("blue", "base", 2, {"small": 12, "medium": 18, "large": 30}),
    ("black", "expansion-1", 4, {"small": 20, "medium": 36, "large": 60}),
]

PERCENT_BONUSES = [
    ("red", "expansion-1", 4, 5),
    ("orange", "expansion-1", 4, 10),
]

TIME_TRAP_TEXT = (
    "Place this card on any transit station and inform the seekers of its location. "
    "Every [S15, M30, L60] minutes, increase this card's value by [S4, M6, L10] "
    "minutes. If the seekers ever visit or pass through the trapped station, remove "
    "this card and add its value to your hiding time.")

# ---------------------------------------------------------------- powerups

POWERUPS = [
    ("Randomize question", "base", 4,
     "Play instead of answering a question. A new unasked question from the same "
     "category is chosen, at random, which you answer instead."),
    ("Veto question", "base", 4,
     "Play instead of answering a question. No answer is given, and no reward is earned."),
    ("Duplicate another card", "base", 2,
     "Play this card as a copy of any other card in your hand. This may be used to "
     "duplicate a time bonus at the end of your round."),
    ("Discard 1, draw 2", "base", 4,
     "Discard one other card from your hand. Then, draw and keep two cards from the "
     "hider deck."),
    ("Discard 2, draw 3", "base", 4,
     "Discard two other cards from your hand. Then, draw and keep three cards from the "
     "hider deck."),
    ("Draw 1, expand 1", "base", 2,
     "Draw one card from the hider deck. For the rest of the round, you can hold one "
     "additional card in your hand."),
    ("Move", "base", 1,
     "Discard your hand and send the hiders the location of your transit station. This "
     "card grants a [S10, M20, L60] minute period to establish a new hiding zone "
     "somewhere else on the game map. The seekers are frozen and your hiding timer is "
     "paused until this new hiding period has concluded. This card cannot be played "
     "during the endgame."),
    ("Discard 3, draw 4", "expansion-1", 4,
     "Discard three other cards from your hand. Then, draw and keep four cards from the "
     "hider deck."),
    ("Draw 2, expand 2", "expansion-1", 2,
     "Draw two cards from the hider deck. For the rest of the round, you can hold two "
     "additional cards in your hand."),
    ("Discard me", "expansion-1", 2,
     "You can choose to discard this card to pay for the entirety of a curse's casting "
     "cost, so long as that card's casting cost involves discarding cards."),
    ("Nothing", "expansion-1", 5,
     "This card does nothing. It cannot be played or used to pay for another card's "
     "casting cost."),
]


def build():
    cards = []

    for colour, card_set, copies, values in TIME_BONUSES:
        cards.append({
            "id": f"time-{colour}",
            "type": "time_bonus",
            "set": card_set,
            "name": f"Time bonus, {colour}",
            "copies": copies,
            "colour": colour,
            "minutes": values,
        })

    for colour, card_set, copies, percent in PERCENT_BONUSES:
        cards.append({
            "id": f"time-percent-{percent}",
            "type": "time_bonus",
            "set": card_set,
            "name": f"Time bonus, {percent}%",
            "copies": copies,
            "colour": colour,
            "percent": percent,
            "text": ("Worth this share of your hiding time, counted before any other "
                     "bonus, so percentage bonuses never compound with each other."),
        })

    cards.append({
        "id": "time-trap",
        "type": "time_trap",
        "set": "expansion-1",
        "name": "Time trap",
        "copies": 5,
        "text": TIME_TRAP_TEXT,
        "sizes": read_sizes(TIME_TRAP_TEXT),
        "text_medium": for_size(TIME_TRAP_TEXT, "medium"),
    })

    for name, card_set, copies, text in POWERUPS:
        card = {
            "id": "powerup-" + slug(name),
            "type": "nothing" if name == "Nothing" else "powerup",
            "set": card_set,
            "name": name,
            "copies": copies,
            "text": text,
        }
        sizes = read_sizes(text)
        if sizes:
            card["sizes"] = sizes
            card["text_medium"] = for_size(text, "medium")
        cards.append(card)

    with open(os.path.join(SOURCE, "curses.csv"), encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            name = " ".join(row["Title"].split())
            text = " ".join((row["Text"] or "").split())
            cost = " ".join((row["Casting Cost"] or "").split())
            notes = " ".join((row["Rule Book Notes"] or "").split())
            card = {
                "id": slug(name),
                "type": "curse",
                "set": "base" if row["Set"] == "Base Game" else "expansion-1",
                "name": name,
                "copies": 1,
                "text": text,
                "casting_cost": cost,
                "notes": None if notes in ("", "—") else notes,
            }
            sizes = read_sizes(text, cost)
            if sizes:
                card["sizes"] = sizes
                card["text_medium"] = for_size(text, "medium")
                card["casting_cost_medium"] = for_size(cost, "medium")
            cards.append(card)

    return cards


def check(cards):
    """Card counts must match the composition tab of the source sheet."""
    expected = {
        ("time_bonus", "base"): 55, ("time_bonus", "expansion-1"): 12,
        ("powerup", "base"): 21, ("powerup", "expansion-1"): 8,
        ("time_trap", "expansion-1"): 5, ("nothing", "expansion-1"): 5,
        ("curse", "base"): 24, ("curse", "expansion-1"): 50,
    }
    actual = {}
    for card in cards:
        key = (card["type"], card["set"])
        actual[key] = actual.get(key, 0) + card["copies"]
    ok = True
    for key in sorted(set(expected) | set(actual)):
        got, want = actual.get(key, 0), expected.get(key, 0)
        flag = "" if got == want else f"  <-- expected {want}"
        if got != want:
            ok = False
        print(f"  {key[0]:11s} {key[1]:12s} {got:4d}{flag}")
    print(f"  {'TOTAL':11s} {'':12s} {sum(actual.values()):4d}")
    return ok


if __name__ == "__main__":
    cards = build()
    ok = check(cards)

    doc = {
        "description": ("Every card in Jet Lag: The Game — Hide and Seek, base game plus "
                        "Expansion Pack Volume 1. `copies` is how many of that card the "
                        "printed sets contain, not how many are in any one deck."),
        "sources": {
            "curse_text": SHEET + " (curses tab)",
            "card_counts": SHEET + " (composition tab)",
            "other_text": "transcribed from the physical cards",
        },
        "size_values": ("Card text contains [S…, M…, L…] triples, one value per game "
                        "size. `sizes` lists them in order and `text_medium` resolves "
                        "them for a medium game."),
        "totals": {
            "cards": sum(c["copies"] for c in cards),
            "distinct": len(cards),
        },
        "cards": cards,
    }
    path = os.path.join(HERE, "cards.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print(f"\nwrote cards.json: {doc['totals']['distinct']} distinct, "
          f"{doc['totals']['cards']} cards" + ("" if ok else "  (COUNT MISMATCH)"))
