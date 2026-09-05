"""
Builds map.html: the network on a real basemap, with Leaflet.

This one is not an Artifact, so it can load map tiles and embed a Google My Map.
Open it from disk or host it anywhere. The data is inlined, so it works from
file:// with no server.

Run: python build_webmap.py
"""

import json
import math
import os

import build_map as M
import build_mapdata as D

HERE = os.path.dirname(os.path.abspath(__file__))
TOLERANCE_DEG = 0.0006  # about 60 m

LINE_HEX = {
    "blue": "#0092d4", "red": "#e02b25", "green": "#00a24c", "pendel": "#e4629b",
    "city": "#a39b92", "nockeby": "#8ca0cb", "orange": "#ef7c22",
    "roslag": "#b587c8", "saltsjo": "#10b0a4",
}
SYSTEM_SWATCH = {"Tunnelbana": "blue", "Pendeltåg": "pendel", "Tram": "orange",
                 "Roslagsbanan": "roslag", "Saltsjöbanan": "saltsjo"}


def payload():
    rows = M.build_rows()
    lines = []
    for line in M.route_lines():
        paths = []
        for way in line["ways"]:
            points = [(round(p["lat"], 5), round(p["lon"], 5)) for p in way]
            trimmed = [points[0]]
            for point in points[1:]:
                if point != trimmed[-1]:
                    trimmed.append(point)
            if len(trimmed) < 2:
                continue
            paths.append([c for point in D.thin(trimmed, TOLERANCE_DEG) for c in point])
        lines.append({"n": line["name"], "c": line["colour"],
                      "s": M.SYSTEM_OF[line["colour"]], "p": paths})

    stops = [[r["name"], r["lines"], r["kommun"], r["system"].split(" + ")[0],
              round(r["lat"], 5), round(r["lon"], 5)] for r in rows]

    return {"centre": list(M.BORDER_CENTRE), "radius": M.BORDER_RADIUS_KM * 1000,
            "zone": M.ZONE_RADIUS_M,
            "zones": [[radius, label.split(" — ")[0]] for radius, label in M.ZONE_VARIANTS],
            "lines": lines, "stops": stops,
            "colours": LINE_HEX, "swatches": SYSTEM_SWATCH,
            "lineColour": M.LINE_COLOURS}


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stockholm Hide &amp; Seek — map</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root {
    --bg: #e9eef2; --surface: #fff; --surface-2: #f4f7f9;
    --ink: #0e1620; --ink-soft: #35434f; --muted: #5c6b7a;
    --rule: #d3dde4; --rule-strong: #b6c4ce; --accent: #0079b8; --flag: #14324f;
    --display: "Familjen Grotesk", Helvetica, Arial, sans-serif;
    --body: "IBM Plex Sans", "Segoe UI", system-ui, sans-serif;
    --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0a0f14; --surface: #121a21; --surface-2: #18222b;
      --ink: #e8eef4; --ink-soft: #c2cedb; --muted: #91a1b0;
      --rule: #22303b; --rule-strong: #334654; --accent: #3aabe8; --flag: #17334d;
    }
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: var(--body); font-size: 15px;
    display: flex; flex-direction: column;
  }
  header {
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 10px 14px; border-bottom: 1px solid var(--rule); background: var(--surface);
  }
  h1 {
    font-family: var(--display); font-weight: 700; font-size: 17px;
    letter-spacing: -.01em; margin: 0;
  }
  .kicker {
    font-family: var(--mono); font-size: 10.5px; letter-spacing: .16em;
    text-transform: uppercase; color: var(--muted);
  }
  .gap { flex: 1 1 auto; }
  button, .linkbtn {
    font-family: var(--mono); font-size: 11px; letter-spacing: .08em;
    text-transform: uppercase; color: var(--ink-soft); background: var(--surface);
    border: 1px solid var(--rule-strong); border-radius: 3px; padding: 5px 9px;
    cursor: pointer; text-decoration: none; display: inline-block;
  }
  button:hover, .linkbtn:hover { color: var(--ink); border-color: var(--muted); }
  button[aria-pressed="false"] { opacity: .45; }
  .sys { display: inline-flex; align-items: center; gap: 6px; }
  .sys::before {
    content: ""; width: 9px; height: 9px; border-radius: 50%;
    background: var(--swatch, var(--muted));
  }
  #map { flex: 1 1 auto; min-height: 0; background: var(--surface-2); }
  .leaflet-container { font-family: var(--body); background: var(--surface-2); }
  .leaflet-popup-content { margin: 10px 12px; font-size: 14px; }
  .leaflet-popup-content b { font-family: var(--display); font-size: 15px; }
  .chip {
    display: inline-block; font-family: var(--mono); font-size: 11px;
    line-height: 1.7; padding: 0 6px; border-radius: 2px; color: #fff;
    margin: 2px 2px 0 0;
  }
  .chip.pale { color: #10161c; }
  .kommun { color: var(--muted); font-size: 13px; }
  footer {
    padding: 7px 14px; border-top: 1px solid var(--rule); background: var(--surface);
    font-size: 12px; color: var(--muted);
  }
  footer a { color: var(--accent); }
</style>
</head>
<body>
<header>
  <span class="kicker">Hide &amp; Seek</span>
  <h1>Stockholm rail network</h1>
  <span class="gap"></span>
  <span id="filters"></span>
  <button type="button" id="zones" aria-pressed="false">Zones</button>
  <button type="button" id="reset">Reset</button>
</header>
<div id="map"></div>
<footer>
  252 stops, 21 lines, 55 km border. Map data ©
  <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors.
  <span id="mymaps"></span>
</footer>

<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js"></script>
<script id="net" type="application/json">__DATA__</script>
<script>
(function () {
  var data = JSON.parse(document.getElementById("net").textContent);
  var PALE = { city: 1, nockeby: 1, orange: 1, roslag: 1, saltsjo: 1 };

  var map = L.map("map", { zoomControl: true }).setView(data.centre, 9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: ""
  }).addTo(map);

  L.circle(data.centre, {
    radius: data.radius, color: "#c81d24", weight: 2,
    dashArray: "8 6", fill: false, interactive: false
  }).addTo(map);

  var systems = {};
  function layerFor(name) {
    if (!systems[name]) systems[name] = { lines: L.layerGroup().addTo(map),
                                          stops: L.layerGroup().addTo(map), on: true };
    return systems[name];
  }

  data.lines.forEach(function (line) {
    var colour = data.colours[line.c];
    line.p.forEach(function (flat) {
      var pts = [];
      for (var i = 0; i < flat.length; i += 2) pts.push([flat[i], flat[i + 1]]);
      L.polyline(pts, { color: colour, weight: 3, opacity: .9 })
        .bindTooltip(line.n, { sticky: true })
        .addTo(layerFor(line.s).lines);
    });
  });

  var zoneLayer = L.layerGroup();
  var dots = [];
  data.stops.forEach(function (stop) {
    var first = stop[1].split("/")[0];
    var key = data.lineColour[first] || "muted";
    var colour = data.colours[key] || "#5c6b7a";
    var chips = stop[1].split("/").map(function (line) {
      var k = data.lineColour[line];
      return '<span class="chip' + (PALE[k] ? " pale" : "") + '" style="background:' +
             (data.colours[k] || "#5c6b7a") + '">' + line + "</span>";
    }).join("");

    dots.push(L.circleMarker([stop[4], stop[5]], {
      radius: 4, color: "#fff", weight: 1.5, fillColor: colour, fillOpacity: 1
    }).bindPopup("<b>" + stop[0] + "</b><br>" + chips +
                 '<br><span class="kommun">' + stop[2] + " kommun</span>")
      .bindTooltip(stop[0], { direction: "top" })
      .addTo(layerFor(stop[3]).stops));

    L.circle([stop[4], stop[5]], {
      radius: data.zone, color: "#0079b8", weight: 1, opacity: .5,
      fillOpacity: .08, interactive: false
    }).addTo(zoneLayer);
  });

  // 252 dots at a fixed size turn the middle of the map into one blob when zoomed out
  function sizeDots() {
    var zoom = map.getZoom();
    var radius = zoom <= 9 ? 3 : zoom <= 11 ? 4 : zoom <= 13 ? 5 : 7;
    dots.forEach(function (dot) { dot.setRadius(radius); });
  }
  map.on("zoomend", sizeDots);
  sizeDots();

  var bar = document.getElementById("filters");
  Object.keys(data.swatches).forEach(function (name) {
    if (!systems[name]) return;
    var button = document.createElement("button");
    button.className = "sys";
    button.type = "button";
    button.textContent = name;
    button.setAttribute("aria-pressed", "true");
    button.style.setProperty("--swatch", data.colours[data.swatches[name]]);
    button.addEventListener("click", function () {
      var entry = systems[name];
      entry.on = !entry.on;
      button.setAttribute("aria-pressed", String(entry.on));
      ["lines", "stops"].forEach(function (part) {
        if (entry.on) map.addLayer(entry[part]); else map.removeLayer(entry[part]);
      });
    });
    bar.appendChild(button);
  });

  var zonesButton = document.getElementById("zones");
  zonesButton.addEventListener("click", function () {
    var on = zonesButton.getAttribute("aria-pressed") === "true";
    zonesButton.setAttribute("aria-pressed", String(!on));
    if (on) map.removeLayer(zoneLayer); else zoneLayer.addTo(map);
  });

  document.getElementById("reset").addEventListener("click", function () {
    map.setView(data.centre, 9);
  });
})();
</script>
</body>
</html>
"""


def build():
    doc = payload()
    html = PAGE.replace("__DATA__", json.dumps(doc, ensure_ascii=False,
                                               separators=(",", ":")))
    path = os.path.join(HERE, "map.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"{len(doc['stops'])} stops, {len(doc['lines'])} lines")
    print(f"wrote map.html ({os.path.getsize(path) / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
