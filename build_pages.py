"""
Builds both copies of the field manual from one template.

    docs/index.html   the hosted page, with our Google My Map embedded.
    field-manual.html the Artifact copy, which cannot load an iframe, so the map
                      is a link instead.

Run: python build_pages.py
"""

import csv
import html
import json
import os

import build_coast
import build_map as M
import figures

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "page-template.html")
CARDS = os.path.join(HERE, "cards", "cards.json")
STATIONS = os.path.join(HERE, "data", "stations.csv")

SITE = "https://monolu.github.io/jetlag-stockholm/"
MYMAPS_ID = "1KjLl3dy7DhmggT4o4qT-awV80zBs7t0"
MYMAPS_VIEW = "https://www.google.com/maps/d/viewer?mid=" + MYMAPS_ID + "&hl=en"
MYMAPS_EMBED = ("https://www.google.com/maps/d/embed?mid=" + MYMAPS_ID +
                "&amp;hl=en&amp;ll=59.35%2C17.92&amp;z=10")

SYSTEMS = ["Tunnelbana", "Pendeltåg", "Tram", "Roslagsbanan", "Saltsjöbanan"]
SWATCH = {"Tunnelbana": "blue", "Pendeltåg": "pendel", "Tram": "orange",
          "Roslagsbanan": "roslag", "Saltsjöbanan": "saltsjo"}
CHIP = {"blue": "c-blue", "red": "c-red", "green": "c-green", "pendel": "c-pendel",
        "city": "c-city", "nockeby": "c-nockeby", "orange": "c-orange",
        "roslag": "c-roslag", "saltsjo": "c-saltsjo"}

# The powerups carry no notes column in the card spreadsheet; these are the
# rulebook's own explanations, from lifack.ch/docs/hiding/the_hider_deck/powerups
# and the expansion reference rules.
POWERUP_NOTES = {
    "Veto question": (
        "Played in response to a question instead of answering. The seekers are told a "
        "veto was used. The question still counts as asked, so asking it again costs the "
        "doubled price, and the hiders draw nothing for it."),
    "Randomize question": (
        "Played in response to a question instead of answering. The seekers pick a "
        "different unasked question from the same category at random, by dice or "
        "generator, and that one is answered instead. The original question does not "
        "count as asked. A random pick that lands on a null answer still stands."),
    "Duplicate another card": (
        "Copies any card in hand: curse, powerup or time bonus. The original stays in "
        "hand and can still be played. Left in hand at the end of a round it copies a "
        "time bonus, doubling it."),
    "Discard 1, draw 2": (
        "Playable at any time. It leaves the hand as it is played, so the hand ends the "
        "same size it started. It cannot be played without enough cards to discard."),
    "Discard 2, draw 3": (
        "Playable at any time. It leaves the hand as it is played, so the hand ends the "
        "same size it started. It cannot be played without enough cards to discard."),
    "Discard 3, draw 4": (
        "Playable at any time. It leaves the hand as it is played, so the hand ends the "
        "same size it started. It cannot be played without enough cards to discard."),
    "Draw 1, expand 1": (
        "Draws a card and raises the hand limit by one for the rest of the round. Two of "
        "them stack to eight."),
    "Draw 2, expand 2": (
        "Draws two cards and raises the hand limit by two for the rest of the round."),
    "Discard me": (
        "Pays a curse's whole casting cost on its own, as long as that cost is discarding "
        "cards."),
    "Move": (
        "Discard the hand, tell the seekers the station, then 20 minutes to build a new "
        "zone anywhere on the map. The seekers are frozen and the hiding clock is paused "
        "for those 20 minutes, then it carries on from where it stopped. It cannot be "
        "played during the end game."),
    "Time trap": (
        "Goes on a station that is part of our network, one of the 235, and the seekers "
        "are told where. It leaves the hand as it is placed. Passing through means "
        "travelling a line that runs through that station."),
    "Nothing": "Does nothing. It cannot be played, and it cannot pay a casting cost.",
}

FIGURES = figures.build()
FIGURES['FIG-COAST'] = build_coast.figure()[0]

SITE_MAP = """      <div class="mapwrap">
        <iframe id="mymaps" title="Our game map in Google My Maps" loading="lazy"
                allowfullscreen src="__EMBED__"></iframe>
        <div class="mapout">
          <a href="__VIEW__" target="_blank" rel="noopener">Open in Google Maps</a>
          <span>On a phone it opens in the Google Maps app, where you can search and get
            directions.</span>
        </div>
      </div>
"""

ARTIFACT_MAP = """      <p>The map is a Google My Map, which an Artifact cannot load.
        <a href="__VIEW__" target="_blank" rel="noopener">Open it in Google Maps</a>, or read
        this page with the map in place at <a href="__SITE__">monolu.github.io/jetlag-stockholm</a>.</p>
"""

SITE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Rules, map and all 235 stops for our Stockholm hide and seek game.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128647;</text></svg>">
<style>
  html { color-scheme: light dark; }
  body { margin: 0; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
"""


def read_stops():
    with open(STATIONS, encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def chips(row):
    out = []
    for line in row["lines"].split("/"):
        out.append(f'<span class="chip {CHIP[M.LINE_COLOURS[line]]}">{line}</span>')
    return " ".join(out)


def stop_rows(rows):
    out = []
    for row in rows:
        key = f"{row['name']} {row['lines']} {row['kommun']} {row['system']}".lower()
        out.append(
            f'            <tr data-k="{html.escape(key, quote=True)}" '
            f'data-sys="{html.escape(row["system"].split(" + ")[0], quote=True)}">'
            f'<td class="name nowrap">{html.escape(row["name"])}</td>'
            f"<td>{chips(row)}</td>"
            f'<td class="nowrap">{html.escape(row["kommun"])}</td></tr>')
    return "\n".join(out)


def system_tabs(rows):
    counts = {}
    for row in rows:
        first = row["system"].split(" + ")[0]
        counts[first] = counts.get(first, 0) + 1
    out = ['        <button type="button" role="tab" class="all" aria-selected="true">'
           f"All {len(rows)}</button>"]
    for system in SYSTEMS:
        if system not in counts:
            continue
        out.append(
            f'        <button type="button" role="tab" data-sys="{html.escape(system, quote=True)}" '
            f'aria-selected="false" style="--swatch: var(--{SWATCH[system]})">'
            f"{html.escape(system)} {counts[system]}</button>")
    return "\n".join(out)


def clarify_rows():
    cards = json.load(open(CARDS, encoding="utf-8"))["cards"]
    entries = []
    for card in cards:
        note = POWERUP_NOTES.get(card["name"]) or card.get("notes")
        if not note:
            continue
        entries.append((card["name"], note))
    entries.sort(key=lambda e: e[0].lower())
    out = []
    for name, note in entries:
        key = f"{name} {note}".lower()
        out.append(
            f'            <tr data-k="{html.escape(key, quote=True)}">'
            f'<td class="name nowrap">{html.escape(name)}</td>'
            f"<td>{html.escape(note)}</td></tr>")
    return "\n".join(out), len(entries)


def fill(page, pairs):
    for key, value in pairs.items():
        marker = f"<!--{key}-->"
        assert marker in page, "missing marker " + marker
        page = page.replace(marker, value)
    return page


def build():
    rows = read_stops()
    template = open(TEMPLATE, encoding="utf-8").read()
    clarify, n_clarify = clarify_rows()

    common = dict(FIGURES)
    common.update({
        "STOPS": stop_rows(rows),
        "SYSTABS": system_tabs(rows),
        "CLARIFY": clarify,
    })

    artifact = fill(template, dict(common, MAPBLOCK=(
        ARTIFACT_MAP.replace("__VIEW__", MYMAPS_VIEW).replace("__SITE__", SITE))))
    with open(os.path.join(HERE, "field-manual.html"), "w", encoding="utf-8") as fh:
        fh.write(artifact)

    site = fill(template, dict(common, MAPBLOCK=(
        SITE_MAP.replace("__EMBED__", MYMAPS_EMBED).replace("__VIEW__", MYMAPS_VIEW))))
    # the title, fonts and stylesheet belong in a real <head>
    cut = site.index("</style>") + len("</style>")
    site = SITE_HEAD + site[:cut] + "\n</head>\n<body>\n" + site[cut:] + "\n</body>\n</html>\n"
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    with open(os.path.join(HERE, "docs", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(site)

    print(f"{len(rows)} stops, {n_clarify} card clarifications")
    for name in ("field-manual.html", os.path.join("docs", "index.html")):
        print(f"wrote {name} ({os.path.getsize(os.path.join(HERE, name)) / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
