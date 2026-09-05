"""
Builds docs/index.html: the field manual as a normal web page.

The Artifact copy has to draw its own map, because an Artifact cannot load map
tiles or embed an iframe. A hosted page can, so this build swaps the drawn map
for our Google My Map — the same basemap we use during the game, with every
landmark Google knows about.

Run: python build_site.py
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "field-manual.html")
OUT = os.path.join(HERE, "docs", "index.html")

MYMAPS_ID = "1KjLl3dy7DhmggT4o4qT-awV80zBs7t0"
MYMAPS_VIEW = "https://www.google.com/maps/d/viewer?mid=" + MYMAPS_ID

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stockholm Hide &amp; Seek</title>
<meta name="description" content="Rules, map and all 252 stops for our Stockholm hide and seek game.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128647;</text></svg>">
<style>
  html { color-scheme: light dark; }
  body { margin: 0; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
</head>
<body>
"""

SITE_CSS = """
  /* ---------- embedded map ---------- */
  #mymaps {
    display: block;
    width: 100%;
    height: clamp(420px, 70vh, 720px);
    border: 0;
  }

  .mapout {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    border-top: 1px solid var(--rule);
    padding: 10px 12px;
    font-size: 13.5px;
    color: var(--muted);
  }

  .mapout a {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: .08em;
    text-transform: uppercase;
    color: var(--ink-soft);
    background: var(--surface);
    border: 1px solid var(--rule-strong);
    border-radius: 3px;
    padding: 5px 9px;
    text-decoration: none;
  }

  .mapout a:hover { color: var(--ink); border-color: var(--muted); }
"""

MAP_BLOCK = """      <div class="mapwrap">
        <iframe id="mymaps" src="https://www.google.com/maps/d/embed?mid=__MID__&amp;ll=59.38%2C17.79&amp;z=9"
                title="Our game map in Google My Maps" allowfullscreen></iframe>
        <div class="mapout">
          <a href="__VIEW__" target="_blank" rel="noopener">Open in Google Maps</a>
          <span>Opens in the Google Maps app on a phone, where you can search and get directions.</span>
        </div>
      </div>
"""


def build():
    page = open(TEMPLATE, encoding="utf-8").read()

    # the drawn map and its controls give way to the embed
    start = page.index('      <div class="mapwrap">')
    end = page.index("      <p>The dashed circle is the border.")
    block = MAP_BLOCK.replace("__MID__", MYMAPS_ID).replace("__VIEW__", MYMAPS_VIEW)
    page = page[:start] + block + page[end:]

    page = page.replace(
        """      <p>The dashed circle is the border. Turning on <em class="q">Zones</em> draws the
        400 m hiding zone around every stop; they are specks until you zoom in.</p>""",
        """      <p>The layers are the border, the 21 lines, all 252 stops and a 400 m hiding zone
        around each of them. Open the panel at the top left of the map to turn layers on
        and off; the zones are specks until you zoom in.</p>""")

    page = page.replace(
        """      <p>Every line, every stop and the border, drawn from the same data as the tables
        below. Drag to pan, scroll or pinch to zoom, tap a stop to read it.</p>""",
        """      <p>Our Google My Map, on the same basemap we use during the game. Every line,
        every stop and the border, drawn from the same data as the tables below.</p>""")

    # the drawn map's payload and code go with it
    page = re.sub(r'<script type="application/json" id="map-data">.*?</script>\s*',
                  "", page, flags=re.S)
    start = page.index("<script>")
    keep = page.index('  (function () {\n    var q = document.getElementById("q");')
    page = page[:start] + "<script>\n" + page[keep:]

    # the drawn map's styles have nothing left to style
    css_start = page.index("  /* ---------- network map ---------- */")
    css_end = page.index("  /* ---------- definition callout ---------- */")
    page = page[:css_start] + page[css_end:]

    page = page.replace("  /* ---------- definition callout ---------- */",
                        SITE_CSS + "\n  /* ---------- definition callout ---------- */", 1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(HEAD + page + "\n</body>\n</html>\n")
    print(f"wrote docs/index.html ({os.path.getsize(OUT) / 1024:.0f} KB), My Map {MYMAPS_ID}")


if __name__ == "__main__":
    build()
