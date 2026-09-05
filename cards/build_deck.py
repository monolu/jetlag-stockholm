"""
Builds or checks a hider deck from cards.json.

The printed sets hold 180 cards. A deck is a subset of them, mixed to roughly
50% time bonuses, 25% curses and 25% powerups.

    python build_deck.py                      # a 100 card deck, seed 1
    python build_deck.py --size 120 --seed 7
    python build_deck.py --check deck-stockholm.json

Time traps count towards the time bonus share; "Nothing" cards count towards the
powerups. Within each share, cards are drawn in proportion to how many of them the
printed sets contain, so a deck keeps the shape of the real one: plenty of red,
one Move, and so on. Curses are drawn at random, one copy each.
"""

import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
SHARES = {"time": 0.50, "curse": 0.25, "powerup": 0.25}
GROUP_OF = {"time_bonus": "time", "time_trap": "time",
            "powerup": "powerup", "nothing": "powerup", "curse": "curse"}


def load_cards():
    with open(os.path.join(HERE, "cards.json"), encoding="utf-8") as fh:
        return {c["id"]: c for c in json.load(fh)["cards"]}


def largest_remainder(weights, total):
    """Split `total` across `weights` so the parts are whole numbers that sum right."""
    if not weights or total <= 0:
        return {key: 0 for key in weights}
    pool = sum(weights.values())
    exact = {key: total * weight / pool for key, weight in weights.items()}
    out = {key: int(value) for key, value in exact.items()}
    short = total - sum(out.values())
    order = sorted(exact, key=lambda key: (-(exact[key] - out[key]), key))
    for key in order[:short]:
        out[key] += 1
    return out


def build(cards, size, seed):
    rng = random.Random(seed)
    targets = largest_remainder({g: SHARES[g] for g in SHARES}, size)

    deck = {}
    for group in ("time", "powerup"):
        pool = {cid: c["copies"] for cid, c in cards.items()
                if GROUP_OF[c["type"]] == group}
        for cid, copies in largest_remainder(pool, targets[group]).items():
            capped = min(copies, cards[cid]["copies"])
            if capped:
                deck[cid] = capped
        # rounding can leave the group a card short of its target
        while sum(deck[c] for c in deck if GROUP_OF[cards[c]["type"]] == group) < targets[group]:
            room = [cid for cid in pool if deck.get(cid, 0) < cards[cid]["copies"]]
            if not room:
                break
            pick = max(room, key=lambda cid: (cards[cid]["copies"], cid))
            deck[pick] = deck.get(pick, 0) + 1

    curses = sorted(cid for cid, c in cards.items() if c["type"] == "curse")
    rng.shuffle(curses)
    for cid in curses[:targets["curse"]]:
        deck[cid] = 1

    return deck, targets


def summarise(cards, deck):
    counts = {"time": 0, "curse": 0, "powerup": 0}
    for cid, copies in deck.items():
        counts[GROUP_OF[cards[cid]["type"]]] += copies
    total = sum(counts.values())
    print(f"{total} cards")
    for group in ("time", "curse", "powerup"):
        share = counts[group] / total * 100 if total else 0
        print(f"  {group:8s} {counts[group]:4d}   {share:4.1f}%   target {SHARES[group] * 100:.0f}%")
    return counts


def write(cards, deck, path, note):
    doc = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "note": note,
        "size": sum(deck.values()),
        "cards": [{"id": cid, "name": cards[cid]["name"], "copies": deck[cid]}
                  for cid in sorted(deck, key=lambda c: (GROUP_OF[cards[c]["type"]],
                                                         cards[c]["type"], c))],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print("wrote", os.path.relpath(path, HERE))


def check(cards, path):
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    deck, bad = {}, []
    for entry in doc["cards"]:
        card = cards.get(entry["id"])
        if card is None:
            bad.append(f"unknown id: {entry['id']}")
            continue
        if entry["copies"] > card["copies"]:
            bad.append(f"{entry['id']}: {entry['copies']} copies, sets only hold {card['copies']}")
        if entry.get("name") and entry["name"] != card["name"]:
            bad.append(f"{entry['id']}: name is {card['name']!r}")
        deck[entry["id"]] = entry["copies"]
    print(doc.get("name", path))
    summarise(cards, deck)
    for problem in bad:
        print("  !", problem)
    return not bad


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--out", default=os.path.join(HERE, "deck.json"))
    parser.add_argument("--check")
    args = parser.parse_args()

    cards = load_cards()
    if args.check:
        raise SystemExit(0 if check(cards, args.check) else 1)

    deck, _ = build(cards, args.size, args.seed)
    summarise(cards, deck)
    write(cards, deck, args.out, f"generated at size {args.size}, seed {args.seed}")
