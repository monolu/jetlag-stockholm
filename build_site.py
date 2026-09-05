"""
Builds docs/index.html: the field manual as a normal web page.

Same content as the Artifact, but a normal page can load map tiles, so the drawn
SVG map is swapped for a Leaflet map on OpenStreetMap. Set MYMAPS_ID to the id in
a Google My Maps share link and the page gains a tab for it; an Artifact cannot
embed one, a hosted page can.

Run: python build_site.py
"""

import json
import os
import re

import build_webmap as W

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "field-manual.html")
OUT = os.path.join(HERE, "docs", "index.html")

MYMAPS_ID = None  # e.g. "1AbCdEf..." from https://www.google.com/maps/d/edit?mid=...

HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="colour-scheme" content="light dark">
<title>Stockholm Hide &amp; Seek</title>
<meta name="description" content="Rules, map and all 252 stops for our Stockholm hide and seek game.">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><text y='26' font-size='26'>&#128647;</text></svg>">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<style>
  html { color-scheme: light dark; }
  body { margin: 0; }
  img { max-width: 100%; }
  [hidden] { display: none !important; }
</style>
"""

SITE_CSS = """
  /* ---------- hosted map ---------- */
  #netmap { height: clamp(380px, 66vh, 680px); width: 100%; }
  .leaflet-container { font-family: var(--body); background: var(--surface-2); }
  .leaflet-popup-content { margin: 10px 12px; font-size: 14px; color: #10161c; }
  .leaflet-popup-content b { font-family: var(--display); font-size: 15px; }
  .leaflet-popup-content .kommun { color: #5c6b7a; font-size: 13px; }
  .leaflet-control-attribution { font-size: 10px; }
  .mapframe { padding: 0; }
  #mymaps-frame { width: 100%; height: clamp(380px, 66vh, 680px); border: 0; display: block; }
"""

LEAFLET_JS = """
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
            ' &nbsp;<span class="count">' + stop[2] + "</span>";
        }
      });

      dots.push(marker);
      L.circle([stop[4], stop[5]], {
        radius: data.zone, color: "#0079b8", weight: 1, opacity: .5,
        fillOpacity: .08, interactive: false
      }).addTo(zoneLayer);
    });

    // 252 dots at a fixed size turn the middle into one blob when zoomed out
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
  })();
"""


def build():
    page = open(TEMPLATE, encoding="utf-8").read()

    # the drawn map becomes a Leaflet container
    page = re.sub(r'<svg id="netmap"[^>]*>\s*</svg>', '<div id="netmap"></div>', page)

    # swap the SVG payload for lat/lon, which is what Leaflet wants
    payload = json.dumps(W.payload(), ensure_ascii=False, separators=(",", ":"))
    page = re.sub(r'(<script type="application/json" id="map-data">).*?(</script>)',
                  lambda m: m.group(1) + payload + m.group(2), page, flags=re.S)

    # drop the SVG drawing code, keep the stop filter and the section rail
    start = page.index("<script>")
    keep_from = page.index('  (function () {\n    var q = document.getElementById("q");')
    page = page[:start] + "<script>\n" + LEAFLET_JS + "\n" + page[keep_from:]

    page = page.replace("  /* ---------- definition callout ---------- */",
                        SITE_CSS + "\n  /* ---------- definition callout ---------- */", 1)

    page = page.replace(
        "<p>Every line, every stop and the border, drawn from the same data as the tables\n"
        "        below. Drag to pan, scroll or pinch to zoom, tap a stop to read it.</p>",
        "<p>Every line, every stop and the border, on the real map. Drag to pan, scroll or "
        "pinch to zoom, tap a stop for its lines and kommun.</p>")

    if MYMAPS_ID:
        embed = ('<iframe id="mymaps-frame" loading="lazy" title="Our Google My Map" '
                 'src="https://www.google.com/maps/d/embed?mid=' + MYMAPS_ID + '"></iframe>')
        page = page.replace('<div id="netmap"></div>',
                            '<div id="netmap"></div>' + embed, 1)

    body = ("</head>\n<body>\n" + page +
            '\n<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>'
            "\n</body>\n</html>\n")

    # Leaflet has to be defined before our script runs, so move the tag above it
    body = body.replace(
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>\n</body>',
        "</body>")
    head = HEAD + '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>\n'

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(head + body)
    print(f"wrote docs/index.html ({os.path.getsize(OUT) / 1024:.0f} KB)"
          + ("" if MYMAPS_ID else "   (no My Maps id set)"))


if __name__ == "__main__":
    build()
