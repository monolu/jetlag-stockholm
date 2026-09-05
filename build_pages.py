"""
Builds both copies of the field manual from one template.

    docs/index.html   the hosted page. Tabs between our own Leaflet map and the
                      Google My Map, because a normal page can load tiles and
                      iframes.
    field-manual.html the Artifact copy, which can do neither, so it draws the
                      network itself.

Run: python build_pages.py
"""

import csv
import html
import json
import os
import re

import build_map as M
import build_webmap as W

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "page-template.html")
CARDS = os.path.join(HERE, "cards", "cards.json")
STATIONS = os.path.join(HERE, "data", "stations.csv")

MYMAPS_ID = "1KjLl3dy7DhmggT4o4qT-awV80zBs7t0"
MYMAPS_VIEW = "https://www.google.com/maps/d/viewer?mid=" + MYMAPS_ID + "&hl=en"
MYMAPS_EMBED = ("https://www.google.com/maps/d/embed?mid=" + MYMAPS_ID +
                "&amp;hl=en&amp;ll=59.35%2C17.92&amp;z=10")
LEAFLET = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4"

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

FIGURES = {
    "FIG-MATCHING": """<svg viewBox="0 0 200 140" role="img" aria-label="Matching splits the map in two">
  <path d="M100 8 A62 62 0 0 1 100 132 Z" fill="var(--accent)" fill-opacity=".14"/>
  <circle cx="100" cy="70" r="62" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <line x1="100" y1="8" x2="100" y2="132" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 4"/>
  <circle cx="66" cy="52" r="4" fill="var(--ink)"/><circle cx="132" cy="88" r="4" fill="var(--ink)"/>
  <path d="M124 46 l3 7 8 1 -6 5 2 8 -7-4 -7 4 2-8 -6-5 8-1z" fill="var(--red)"/>
</svg>""",
    "FIG-MEASURING": """<svg viewBox="0 0 200 140" role="img" aria-label="Measuring cuts at the seekers' distance">
  <clipPath id="mclip"><circle cx="100" cy="70" r="62"/></clipPath>
  <g clip-path="url(#mclip)"><circle cx="52" cy="70" r="52" fill="var(--accent)" fill-opacity=".14"/></g>
  <circle cx="100" cy="70" r="62" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <circle cx="52" cy="70" r="52" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 4"/>
  <circle cx="52" cy="70" r="4" fill="var(--ink)"/>
  <path d="M96 62 l3 7 8 1 -6 5 2 8 -7-4 -7 4 2-8 -6-5 8-1z" fill="var(--red)"/>
</svg>""",
    "FIG-RADAR": """<svg viewBox="0 0 200 140" role="img" aria-label="Radar draws a circle around the seekers">
  <circle cx="100" cy="70" r="62" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <circle cx="100" cy="70" r="34" fill="var(--accent)" fill-opacity=".14" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 4"/>
  <line x1="100" y1="70" x2="134" y2="70" stroke="var(--muted)" stroke-width="1.5"/>
  <path d="M96 62 l3 7 8 1 -6 5 2 8 -7-4 -7 4 2-8 -6-5 8-1z" fill="var(--red)"/>
</svg>""",
    "FIG-TENTACLE": """<svg viewBox="0 0 200 140" role="img" aria-label="A tentacle question leaves one wedge">
  <circle cx="100" cy="70" r="62" fill="none" stroke="var(--rule-strong)" stroke-width="2"/>
  <circle cx="100" cy="70" r="40" fill="none" stroke="var(--accent)" stroke-width="2" stroke-dasharray="5 4"/>
  <path d="M100 70 L140 70 A40 40 0 0 1 108 109 Z" fill="var(--accent)" fill-opacity=".2"/>
  <circle cx="122" cy="92" r="4" fill="var(--ink)"/>
  <circle cx="74" cy="52" r="4" fill="var(--muted)"/><circle cx="86" cy="102" r="4" fill="var(--muted)"/>
  <path d="M96 62 l3 7 8 1 -6 5 2 8 -7-4 -7 4 2-8 -6-5 8-1z" fill="var(--red)"/>
</svg>""",
}

# ---------------------------------------------------------------- the two maps

SVG_MAP_SECTION = """      <p>Every line, every stop and the border, drawn from the same data as the tables
        below. Drag to pan, scroll or pinch to zoom, tap a stop to read it.</p>
      <div class="mapwrap">
        <div class="mapframe">
          <svg id="netmap" role="img"
               aria-label="Map of the SL rail network inside the game border"></svg>
        </div>
        <div class="mapbar" id="mapbar">__SYSBUTTONS__
          <span class="gap"></span>
          <button type="button" id="mapzones" aria-pressed="false">Zones</button>
          <button type="button" id="mapin">Zoom in</button>
          <button type="button" id="mapout">Zoom out</button>
          <button type="button" id="mapreset">Reset</button>
        </div>
        <div class="mapread" id="mapread" aria-live="polite">Tap a stop for its lines and kommun.</div>
      </div>
      <p>The dashed circle is the border. <em class="q">Zones</em> draws the 500 m hiding
        zone around every stop; they are specks until you zoom in. The live page at
        <a href="https://monolu.github.io/jetlag-stockholm/">monolu.github.io/jetlag-stockholm</a>
        carries this on a real basemap and next to our Google My Map, which an Artifact
        cannot load.</p>
"""

LEAFLET_MAP_SECTION = """      <p>Two views of the same game. <em class="q">Network</em> is our own data, with the
        lines in SL's colours and a switch for each system. <em class="q">Google</em> is our
        My Map on Google's basemap, which is where the landmarks the questions ask about
        are.</p>
      <div class="mapwrap">
        <div class="maptabs" role="tablist" aria-label="Which map">
          <button type="button" role="tab" id="tab-net" aria-controls="panel-net" aria-selected="true">Network</button>
          <button type="button" role="tab" id="tab-goo" aria-controls="panel-goo" aria-selected="false">Google</button>
        </div>
        <div id="panel-net" role="tabpanel" aria-labelledby="tab-net">
          <div id="netmap"></div>
          <div class="mapbar" id="mapbar">__SYSBUTTONS__
            <span class="gap"></span>
            <button type="button" id="mapzones" aria-pressed="false">Zones</button>
            <button type="button" id="mapin">Zoom in</button>
            <button type="button" id="mapout">Zoom out</button>
            <button type="button" id="mapreset">Reset</button>
          </div>
          <div class="mapread" id="mapread" aria-live="polite">Tap a stop for its lines and kommun.</div>
        </div>
        <div id="panel-goo" role="tabpanel" aria-labelledby="tab-goo" hidden>
          <iframe id="mymaps" title="Our game map in Google My Maps" allowfullscreen
                  data-src="__EMBED__"></iframe>
          <div class="mapout">
            <a href="__VIEW__" target="_blank" rel="noopener">Open in Google Maps</a>
            <span>Opens in the Google Maps app on a phone, where you can search and get directions.</span>
          </div>
        </div>
      </div>
      <p>The dashed circle is the border. <em class="q">Zones</em> draws the 500 m hiding
        zone around every stop; they are specks until you zoom in. The Google view carries
        the same layers, plus the 250 m and 750 m circles the two zone curses make, toggled
        from the panel at its top left.</p>
"""

MAP_CSS = """
  /* ---------- the map ---------- */
  .mapwrap {
    border: 1px solid var(--rule);
    border-radius: 3px;
    background: var(--surface);
    margin: 0 0 16px;
    overflow: hidden;
  }

  .maptabs {
    display: flex;
    gap: 3px;
    padding: 8px 8px 0;
    background: var(--surface-2);
    border-bottom: 1px solid var(--rule);
  }

  .maptabs button {
    font-family: var(--display);
    font-weight: 600;
    font-size: 13px;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--muted);
    background: transparent;
    border: 1px solid transparent;
    border-bottom: 0;
    border-radius: 3px 3px 0 0;
    padding: 7px 13px;
    cursor: pointer;
  }

  .maptabs button:hover { color: var(--ink); }

  .maptabs button[aria-selected="true"] {
    color: var(--ink);
    background: var(--surface);
    border-color: var(--rule);
  }

  .mapframe { position: relative; background: var(--surface-2); border-bottom: 1px solid var(--rule); }

  #netmap { display: block; width: 100%; height: clamp(360px, 60vh, 620px); }
  svg#netmap { touch-action: none; cursor: grab; }
  svg#netmap.dragging { cursor: grabbing; }
  svg#netmap .border { fill: none; stroke: var(--rule-strong); stroke-width: 2; stroke-dasharray: 8 6; }
  svg#netmap .route { fill: none; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2.5; }
  svg#netmap .zone { fill: var(--accent); fill-opacity: .1; stroke: var(--accent); stroke-opacity: .5; stroke-width: 1; }
  svg#netmap circle.stop { r: var(--dot, 400px); stroke: var(--surface); stroke-width: 1; }
  svg#netmap circle.pick { stroke: var(--ink); stroke-width: 2; }
  svg#netmap .off { display: none; }
  svg#netmap text {
    font-family: var(--body);
    font-weight: 600;
    fill: var(--ink);
    paint-order: stroke;
    stroke: var(--surface);
    stroke-width: 4px;
    stroke-linejoin: round;
  }

  #mymaps { display: block; width: 100%; height: clamp(360px, 60vh, 620px); border: 0; }
  .leaflet-container { font-family: var(--body); background: var(--surface-2); }
  .leaflet-popup-content { margin: 10px 12px; font-size: 15px; color: #202937; }
  .leaflet-popup-content b { font-family: var(--display); font-weight: 700; font-size: 16px; }
  .leaflet-popup-content .kommun { color: #6b7688; font-size: 14px; }
  .leaflet-control-attribution { font-size: 10px; }

  .mapbar {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    padding: 9px 11px;
  }

  .mapbar button {
    font-family: var(--display);
    font-weight: 600;
    font-size: 12.5px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--ink-soft);
    background: var(--surface);
    border: 1px solid var(--rule-strong);
    border-radius: 3px;
    padding: 5px 9px;
    cursor: pointer;
  }

  .mapbar button:hover { color: var(--ink); border-color: var(--muted); }
  .mapbar button[aria-pressed="false"] { opacity: .45; }
  .mapbar .sys { display: inline-flex; align-items: center; gap: 6px; }
  .mapbar .sys::before {
    content: "";
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: var(--swatch, var(--muted));
  }
  .mapbar .gap { flex: 1 1 auto; }

  .mapread {
    border-top: 1px solid var(--rule);
    padding: 10px 13px;
    font-size: 15px;
    color: var(--ink-soft);
    min-height: 42px;
  }

  .mapread strong { font-family: var(--display); font-weight: 700; font-size: 17px; }
  .mapread .chip { margin-right: 3px; }

  .mapout {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    border-top: 1px solid var(--rule);
    padding: 10px 12px;
    font-size: 14px;
    color: var(--muted);
  }

  .mapout a {
    font-family: var(--display);
    font-weight: 600;
    font-size: 12.5px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--ink-soft);
    background: var(--surface);
    border: 1px solid var(--rule-strong);
    border-radius: 3px;
    padding: 5px 9px;
    text-decoration: none;
  }
"""

SITE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Rules, map and all 235 stops for our Stockholm hide and seek game.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128647;</text></svg>">
<link rel="stylesheet" href="__LEAFLET__/leaflet.min.css">
<script src="__LEAFLET__/leaflet.js"></script>
<style>
  html { color-scheme: light dark; }
  body { margin: 0; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
""".replace("__LEAFLET__", LEAFLET)


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
        counts[row["system"].split(" + ")[0]] = counts.get(row["system"].split(" + ")[0], 0) + 1
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


def system_buttons():
    out = []
    for system in SYSTEMS:
        out.append(f'\n            <button type="button" data-sys="{html.escape(system, quote=True)}" '
                   f'class="sys" aria-pressed="true">{html.escape(system)}</button>')
    return "".join(out)


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
    payload = json.dumps(W.payload(), ensure_ascii=False, separators=(",", ":"))

    common = dict(FIGURES)
    common.update({
        "STOPS": stop_rows(rows),
        "SYSTABS": system_tabs(rows),
        "CLARIFY": clarify,
        "MAPDATA": payload,
    })

    template = template.replace("  /* ---------- callouts ---------- */",
                                MAP_CSS + "\n  /* ---------- callouts ---------- */", 1)

    svg_js = open(os.path.join(HERE, "js", "map-svg.js"), encoding="utf-8").read()
    leaflet_js = open(os.path.join(HERE, "js", "map-leaflet.js"), encoding="utf-8").read()

    artifact = fill(template, dict(common, **{
        "MAPSECTION": SVG_MAP_SECTION.replace("__SYSBUTTONS__", system_buttons()),
        "MAPSCRIPT": svg_js,
    }))
    with open(os.path.join(HERE, "field-manual.html"), "w", encoding="utf-8") as fh:
        fh.write(artifact)

    site = fill(template, dict(common, **{
        "MAPSECTION": (LEAFLET_MAP_SECTION.replace("__SYSBUTTONS__", system_buttons())
                       .replace("__EMBED__", MYMAPS_EMBED).replace("__VIEW__", MYMAPS_VIEW)),
        "MAPSCRIPT": leaflet_js,
    }))
    site = SITE_HEAD + site + "\n</body>\n</html>\n"
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    with open(os.path.join(HERE, "docs", "index.html"), "w", encoding="utf-8") as fh:
        fh.write(site)

    print(f"{len(rows)} stops, {n_clarify} card clarifications")
    for name in ("field-manual.html", os.path.join("docs", "index.html")):
        print(f"wrote {name} ({os.path.getsize(os.path.join(HERE, name)) / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
