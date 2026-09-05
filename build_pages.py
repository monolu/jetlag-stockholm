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

import build_map as M

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

# The four diagrams, all on one 180-square: the pale disc is the map, the red
# star is the seekers, ink dots are the things a question names, muted dots the
# things it does not, and the shaded ground is what survives the answer.
FIGURES = {
    # the bisector of two things, and the half that holds the seekers' one
    "FIG-MATCHING": """<svg viewBox="0 0 180 180" role="img" aria-label="Matching keeps the half of the map nearest the same thing">
  <clipPath id="clip-match"><circle cx="90" cy="90" r="76"/></clipPath>
  <circle cx="90" cy="90" r="76" fill="var(--surface-2)"/>
  <g clip-path="url(#clip-match)">
    <path d="M45 192 L-10 190 L-10 -10 L133 -8 Z" fill="var(--accent)" fill-opacity=".2"/>
    <line x1="45" y1="192" x2="133" y2="-8" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 5"/>
  </g>
  <circle cx="90" cy="90" r="76" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <circle cx="48" cy="74" r="5" fill="var(--ink)" stroke="var(--surface-2)" stroke-width="2"/>
  <circle cx="130" cy="110" r="5" fill="var(--ink)" stroke="var(--surface-2)" stroke-width="2"/>
  <g transform="translate(62 48)"><path d="M0 -11 L2.7 -3.7 L10.5 -3.4 L4.4 1.4 L6.5 8.9 L0 4.6 L-6.5 8.9 L-4.4 1.4 L-10.5 -3.4 L-2.7 -3.7 Z" fill="var(--red)" stroke="var(--surface-2)" stroke-width="3" paint-order="stroke"/></g>
</svg>""",

    # a circle drawn on the thing, through the seekers: inside it is closer
    "FIG-MEASURING": """<svg viewBox="0 0 180 180" role="img" aria-label="Measuring cuts at the seekers' own distance from the thing">
  <clipPath id="clip-meas"><circle cx="90" cy="90" r="76"/></clipPath>
  <circle cx="90" cy="90" r="76" fill="var(--surface-2)"/>
  <g clip-path="url(#clip-meas)">
    <circle cx="34" cy="90" r="74" fill="var(--accent)" fill-opacity=".2" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 5"/>
  </g>
  <circle cx="90" cy="90" r="76" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <line x1="34" y1="90" x2="108" y2="90" stroke="var(--muted)" stroke-width="1.5"/>
  <circle cx="34" cy="90" r="5" fill="var(--ink)" stroke="var(--surface-2)" stroke-width="2"/>
  <g transform="translate(108 90)"><path d="M0 -11 L2.7 -3.7 L10.5 -3.4 L4.4 1.4 L6.5 8.9 L0 4.6 L-6.5 8.9 L-4.4 1.4 L-10.5 -3.4 L-2.7 -3.7 Z" fill="var(--red)" stroke="var(--surface-2)" stroke-width="3" paint-order="stroke"/></g>
</svg>""",

    "FIG-RADAR": """<svg viewBox="0 0 180 180" role="img" aria-label="Radar draws a circle of the asked size around the seekers">
  <circle cx="90" cy="90" r="76" fill="var(--surface-2)"/>
  <circle cx="84" cy="94" r="40" fill="var(--accent)" fill-opacity=".2" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 5"/>
  <circle cx="90" cy="90" r="76" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <line x1="84" y1="94" x2="124" y2="94" stroke="var(--muted)" stroke-width="1.5"/>
  <g transform="translate(84 94)"><path d="M0 -11 L2.7 -3.7 L10.5 -3.4 L4.4 1.4 L6.5 8.9 L0 4.6 L-6.5 8.9 L-4.4 1.4 L-10.5 -3.4 L-2.7 -3.7 Z" fill="var(--red)" stroke="var(--surface-2)" stroke-width="3" paint-order="stroke"/></g>
</svg>""",

    # the range divided between the three things in it; one share is shaded
    "FIG-TENTACLE": """<svg viewBox="0 0 180 180" role="img" aria-label="A tentacle question leaves the share of the range nearest one thing">
  <circle cx="90" cy="90" r="76" fill="var(--surface-2)"/>
  <path d="M90 90 L90 40 A50 50 0 0 1 133 115 Z" fill="var(--accent)" fill-opacity=".2"/>
  <circle cx="90" cy="90" r="50" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="6 5"/>
  <g stroke="var(--accent)" stroke-width="1.5" stroke-dasharray="4 4" stroke-opacity=".7">
    <line x1="90" y1="90" x2="90" y2="40"/>
    <line x1="90" y1="90" x2="133" y2="115"/>
    <line x1="90" y1="90" x2="47" y2="115"/>
  </g>
  <circle cx="90" cy="90" r="76" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <circle cx="116" cy="74" r="5" fill="var(--ink)" stroke="var(--surface-2)" stroke-width="2"/>
  <circle cx="90" cy="121" r="5" fill="var(--muted)" stroke="var(--surface-2)" stroke-width="2"/>
  <circle cx="64" cy="74" r="5" fill="var(--muted)" stroke="var(--surface-2)" stroke-width="2"/>
  <g transform="translate(90 90)"><path d="M0 -11 L2.7 -3.7 L10.5 -3.4 L4.4 1.4 L6.5 8.9 L0 4.6 L-6.5 8.9 L-4.4 1.4 L-10.5 -3.4 L-2.7 -3.7 Z" fill="var(--red)" stroke="var(--surface-2)" stroke-width="3" paint-order="stroke"/></g>
</svg>""",
}

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
