"""
Builds docs/index.html: the field manual as a normal web page.

The Artifact copy has to draw its own map, because an Artifact can neither embed
an iframe nor load map tiles. A hosted page can do both, so the map section here
carries two:

  Network  our own data on Leaflet, with per-system toggles and a readout
  Google   our Google My Map, for the landmarks the questions actually refer to

The Google one is a cross-origin iframe, so nothing of ours can restyle it or add
controls to it. That is why both are here rather than one.

Run: python build_site.py
"""

import json
import os
import re

import build_webmap as W

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "field-manual.html")
OUT = os.path.join(HERE, "docs", "index.html")

MYMAPS_ID = "1KjLl3dy7DhmggT4o4qT-awV80zBs7t0"
MYMAPS_VIEW = "https://www.google.com/maps/d/viewer?mid=" + MYMAPS_ID
LEAFLET = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4"

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stockholm Hide &amp; Seek</title>
<meta name="description" content="Rules, map and all 252 stops for our Stockholm hide and seek game.">
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

SITE_CSS = """
  /* ---------- the two maps ---------- */
  .maptabs {
    display: flex;
    gap: 2px;
    padding: 8px 8px 0;
    background: var(--surface-2);
    border-bottom: 1px solid var(--rule);
  }

  .maptabs button {
    font-family: var(--mono);
    font-size: 11px;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: var(--muted);
    background: transparent;
    border: 1px solid transparent;
    border-bottom: 0;
    border-radius: 3px 3px 0 0;
    padding: 7px 12px;
    cursor: pointer;
  }

  .maptabs button:hover { color: var(--ink); }

  .maptabs button[aria-selected="true"] {
    color: var(--ink);
    background: var(--surface);
    border-color: var(--rule);
    font-weight: 600;
  }

  #netmap { height: clamp(380px, 62vh, 640px); width: 100%; }
  #mymaps { display: block; width: 100%; height: clamp(380px, 62vh, 640px); border: 0; }

  .leaflet-container { font-family: var(--body); background: var(--surface-2); }
  .leaflet-popup-content { margin: 10px 12px; font-size: 14px; color: #10161c; }
  .leaflet-popup-content b { font-family: var(--display); font-size: 15px; }
  .leaflet-popup-content .kommun { color: #5c6b7a; font-size: 13px; }
  .leaflet-control-attribution { font-size: 10px; }

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
        <div class="maptabs" role="tablist" aria-label="Which map">
          <button type="button" role="tab" id="tab-net" aria-controls="panel-net" aria-selected="true">Network</button>
          <button type="button" role="tab" id="tab-goo" aria-controls="panel-goo" aria-selected="false">Google</button>
        </div>

        <div id="panel-net" role="tabpanel" aria-labelledby="tab-net">
          <div id="netmap"></div>
          <div class="mapbar" id="mapbar">
            <button type="button" data-sys="Tunnelbana" class="sys" aria-pressed="true">Tunnelbana</button>
            <button type="button" data-sys="Pendeltåg" class="sys" aria-pressed="true">Pendeltåg</button>
            <button type="button" data-sys="Tram" class="sys" aria-pressed="true">Tram</button>
            <button type="button" data-sys="Roslagsbanan" class="sys" aria-pressed="true">Roslagsbanan</button>
            <button type="button" data-sys="Saltsjöbanan" class="sys" aria-pressed="true">Saltsjöbanan</button>
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
                  data-src="https://www.google.com/maps/d/embed?mid=__MID__&amp;ll=59.38%2C17.79&amp;z=9"></iframe>
          <div class="mapout">
            <a href="__VIEW__" target="_blank" rel="noopener">Open in Google Maps</a>
            <span>Opens in the Google Maps app on a phone, where you can search and get directions.</span>
          </div>
        </div>
      </div>
"""

LEAFLET_JS = """
  var showNetworkMap;

  (function () {
    var host = document.getElementById("netmap");
    var raw = document.getElementById("map-data");
    if (!host || !raw || typeof L === "undefined") return;

    var data = JSON.parse(raw.textContent);
    var PALE = { city: 1, nockeby: 1, orange: 1, roslag: 1, saltsjo: 1 };
    var COLOUR = data.colours;
    var LINE = data.lineColour;

    var map = L.map(host, { zoomControl: true }).setView(data.centre, 9);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

    L.circle(data.centre, {
      radius: data.radius, color: "#c81d24", weight: 2,
      dashArray: "8 6", fill: false, interactive: false
    }).addTo(map);

    var systems = {};
    function layerFor(name) {
      if (!systems[name]) {
        systems[name] = { lines: L.layerGroup().addTo(map),
                          stops: L.layerGroup().addTo(map), on: true };
      }
      return systems[name];
    }

    data.lines.forEach(function (line) {
      line.p.forEach(function (flat) {
        var points = [];
        for (var i = 0; i < flat.length; i += 2) points.push([flat[i], flat[i + 1]]);
        L.polyline(points, { color: COLOUR[line.c], weight: 3, opacity: .9 })
          .bindTooltip(line.n, { sticky: true })
          .addTo(layerFor(line.s).lines);
      });
    });

    var readout = document.getElementById("mapread");
    var zoneLayer = L.layerGroup();
    var dots = [];

    data.stops.forEach(function (stop) {
      var chips = stop[1].split("/").map(function (line) {
        var key = LINE[line];
        return '<span class="chip' + (PALE[key] ? " pale" : "") + '" style="background:' +
               (COLOUR[key] || "#5c6b7a") + '">' + line + "</span>";
      }).join(" ");

      var marker = L.circleMarker([stop[4], stop[5]], {
        radius: 4, color: "#fff", weight: 1.5,
        fillColor: COLOUR[LINE[stop[1].split("/")[0]]] || "#5c6b7a", fillOpacity: 1
      }).bindPopup("<b>" + stop[0] + "</b><br>" + chips +
                   '<br><span class="kommun">' + stop[2] + " kommun</span>")
        .bindTooltip(stop[0], { direction: "top" })
        .addTo(layerFor(stop[3]).stops);

      marker.on("click", function () {
        if (readout) {
          readout.innerHTML = "<strong>" + stop[0] + "</strong> &nbsp;" + chips +
            ' &nbsp;<span class="count">' + stop[2] + " kommun</span>";
        }
      });

      dots.push(marker);
      L.circle([stop[4], stop[5]], {
        radius: data.zone, color: "#0079b8", weight: 1, opacity: .5,
        fillOpacity: .08, interactive: false
      }).addTo(zoneLayer);
    });

    // 252 dots at one size turn the middle of the map into a single blob
    function sizeDots() {
      var zoom = map.getZoom();
      var radius = zoom <= 9 ? 3 : zoom <= 11 ? 4 : zoom <= 13 ? 5 : 7;
      dots.forEach(function (dot) { dot.setRadius(radius); });
    }
    map.on("zoomend", sizeDots);
    sizeDots();

    Array.prototype.forEach.call(document.querySelectorAll("#mapbar .sys"), function (button) {
      var name = button.dataset.sys;
      var swatch = { "Tunnelbana": "blue", "Pendeltåg": "pendel", "Tram": "orange",
                     "Roslagsbanan": "roslag", "Saltsjöbanan": "saltsjo" }[name];
      button.style.setProperty("--swatch", COLOUR[swatch]);
      button.addEventListener("click", function () {
        var entry = systems[name];
        if (!entry) return;
        entry.on = !entry.on;
        button.setAttribute("aria-pressed", String(entry.on));
        ["lines", "stops"].forEach(function (part) {
          if (entry.on) map.addLayer(entry[part]); else map.removeLayer(entry[part]);
        });
      });
    });

    var zonesButton = document.getElementById("mapzones");
    zonesButton.addEventListener("click", function () {
      var on = zonesButton.getAttribute("aria-pressed") === "true";
      zonesButton.setAttribute("aria-pressed", String(!on));
      if (on) map.removeLayer(zoneLayer); else zoneLayer.addTo(map);
    });

    document.getElementById("mapin").addEventListener("click", function () { map.zoomIn(); });
    document.getElementById("mapout").addEventListener("click", function () { map.zoomOut(); });
    document.getElementById("mapreset").addEventListener("click", function () {
      map.setView(data.centre, 9);
    });

    // Leaflet sizes itself when it is created, so it needs telling once the panel
    // has been hidden and shown again
    showNetworkMap = function () { map.invalidateSize(); };
  })();

  (function () {
    var tabs = { net: document.getElementById("tab-net"), goo: document.getElementById("tab-goo") };
    var panels = { net: document.getElementById("panel-net"), goo: document.getElementById("panel-goo") };
    if (!tabs.net || !tabs.goo) return;
    var frame = document.getElementById("mymaps");

    function select(which) {
      Object.keys(tabs).forEach(function (key) {
        var on = key === which;
        tabs[key].setAttribute("aria-selected", String(on));
        panels[key].hidden = !on;
      });
      // the Google map costs a page load, so it waits until someone asks for it
      if (which === "goo" && frame && !frame.src) frame.src = frame.dataset.src;
      if (which === "net" && showNetworkMap) showNetworkMap();
    }

    tabs.net.addEventListener("click", function () { select("net"); });
    tabs.goo.addEventListener("click", function () { select("goo"); });
  })();
"""


def build():
    page = open(TEMPLATE, encoding="utf-8").read()

    start = page.index('      <div class="mapwrap">')
    end = page.index("      <p>The dashed circle is the border.")
    block = MAP_BLOCK.replace("__MID__", MYMAPS_ID).replace("__VIEW__", MYMAPS_VIEW)
    page = page[:start] + block + page[end:]

    page = page.replace(
        """      <p>Every line, every stop and the border, drawn from the same data as the tables
        below. Drag to pan, scroll or pinch to zoom, tap a stop to read it.</p>""",
        """      <p>Two views of the same game. <em class="q">Network</em> is our own data, with
        the lines in SL's colours and a switch for each system. <em class="q">Google</em> is
        our My Map on Google's basemap, which is where the landmarks the questions ask about
        are.</p>""")

    page = page.replace(
        """      <p>The dashed circle is the border. Turning on <em class="q">Zones</em> draws the
        400 m hiding zone around every stop; they are specks until you zoom in.</p>""",
        """      <p>The dashed circle is the border. Turning on <em class="q">Zones</em> draws the
        400 m hiding zone around every stop; they are specks until you zoom in. The Google
        view carries the same layers, toggled from the panel at its top left.</p>""")

    # the payload becomes lat/lon, which is what Leaflet wants
    payload = json.dumps(W.payload(), ensure_ascii=False, separators=(",", ":"))
    page = re.sub(r'(<script type="application/json" id="map-data">).*?(</script>)',
                  lambda m: m.group(1) + payload + m.group(2), page, flags=re.S)

    # swap the SVG drawing code for the Leaflet one, keep the stop filter and rail
    start = page.index("<script>")
    keep = page.index('  (function () {\n    var q = document.getElementById("q");')
    page = page[:start] + "<script>\n" + LEAFLET_JS + "\n" + page[keep:]

    # the SVG map's own styles go with it; the control bar below it is shared
    css_start = page.index("  #netmap {\n")
    css_end = page.index("  .mapbar {")
    page = page[:css_start] + page[css_end:]

    page = page.replace("  /* ---------- definition callout ---------- */",
                        SITE_CSS + "\n  /* ---------- definition callout ---------- */", 1)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(HEAD + page + "\n</body>\n</html>\n")
    print(f"wrote docs/index.html ({os.path.getsize(OUT) / 1024:.0f} KB), My Map {MYMAPS_ID}")


if __name__ == "__main__":
    build()
