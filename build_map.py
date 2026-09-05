"""
Builds the Stockholm Hide & Seek map files from raw OpenStreetMap data.

The game runs on the whole SL rail network: tunnelbana, trams, pendeltåg,
Roslagsbanan and Saltsjöbanan.

Inputs (data/osm/):
    metro.json       - `station=subway` nodes in the Stockholm bbox
    subrels.json     - tunnelbana route relations 10/11/13/14/17/18/19
    subnodes.json    - tagged member nodes of those relations, for line labels
    tram_rels.json   - tram and light rail route relations 7/12/21/30/31
    tram_stops.json  - tagged member nodes and ways of those relations
    rail_members.json- pendeltåg, Roslagsbanan and Saltsjöbanan relations + stops
    route_geom.json  - metro and tram geometry, one relation per line
    rail_geom.json   - commuter rail geometry, one relation per line
    node_kommun.json - {osm node id: kommun}, from admin_level=7 boundaries

Outputs (data/):
    all-layers.kml     - lines + stops + zones + border in one file, four layers.
                         This is the one to import into Google My Maps.
    stations.csv       - flat list of every stop
    stations.kml       - stops only, foldered by system
    transit-lines.kml  - the routes, drawn and coloured
    hiding-zones.kml   - 400 m circle around every stop
    border.kml         - the game border circle
    stations.geojson   - everything, for anything that eats GeoJSON

Run: python build_map.py
"""

import csv
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "osm")
OUT = os.path.join(HERE, "data")

ZONE_RADIUS_M = 400   # 1/4 mile, rounded. Medium game hiding zone.
NAME_MERGE_M = 600    # same name this close is one stop
NEAR_MERGE_M = 300    # a stop this close on another system is one interchange

# A circle holding every stop. The smallest one has a radius of 53.94 km; this is
# rounded up so nothing sits on the line. Furthest stops: Uppsala C, Gröndalsviken.
BORDER_CENTRE = (59.38, 17.79)
BORDER_RADIUS_KM = 55

# Line numbers and colours follow SL's own rail network map. No number is used
# twice across the systems, so the bare number is enough to identify a line.
LINE_COLOURS = {
    "10": "blue", "11": "blue",
    "13": "red", "14": "red",
    "17": "green", "18": "green", "19": "green",
    "40": "pendel", "41": "pendel", "43": "pendel", "48": "pendel",
    "7": "city", "12": "nockeby", "21": "orange", "30": "orange", "31": "orange",
    "27": "roslag", "28": "roslag", "29": "roslag",
    "25": "saltsjo", "26": "saltsjo",
}

# KML wants aabbggrr, not #rrggbb
KML_COLOURS = {
    "blue": "ffd49200",
    "red": "ff2521e0",
    "green": "ff4ca200",
    "pendel": "ff9b62e4",
    "city": "ff929ba3",
    "nockeby": "ffcba08c",
    "orange": "ff227cef",
    "roslag": "ffc887b5",
    "saltsjo": "ffa4b010",
}

SYSTEM_OF = {
    "blue": "Tunnelbana", "red": "Tunnelbana", "green": "Tunnelbana",
    "pendel": "Pendeltåg",
    "city": "Tram", "nockeby": "Tram", "orange": "Tram",
    "roslag": "Roslagsbanan", "saltsjo": "Saltsjöbanan",
}
SYSTEM_ORDER = ["Tunnelbana", "Pendeltåg", "Tram", "Roslagsbanan", "Saltsjöbanan"]

# One relation per line carries the drawn geometry; the opposite direction is a
# near duplicate and is skipped.
GEOM_LINES = {
    6286469: "10", 6286471: "11", 6286473: "13", 6286475: "14",
    6286477: "17", 6286479: "18", 6286481: "19",
    2860815: "7", 3174524: "12", 251504: "21", 5989911: "30", 11997850: "31",
    2836161: "40", 3304342: "41", 3303656: "43", 3304344: "48",
    241405: "27", 241406: "28", 241407: "29",
    251489: "25", 251496: "26",
}

LINE_NAMES = {
    "10": "Blå linjen 10 · Kungsträdgården–Hjulsta",
    "11": "Blå linjen 11 · Kungsträdgården–Akalla",
    "13": "Röda linjen 13 · Norsborg–Ropsten",
    "14": "Röda linjen 14 · Fruängen–Mörby centrum",
    "17": "Gröna linjen 17 · Skarpnäck–Hässelby strand",
    "18": "Gröna linjen 18 · Farsta strand–Hässelby strand",
    "19": "Gröna linjen 19 · Hagsätra–Hässelby strand",
    "40": "Pendeltåg 40 · Uppsala C–Södertälje centrum",
    "41": "Pendeltåg 41 · Märsta–Södertälje centrum",
    "43": "Pendeltåg 43 · Bålsta–Nynäshamn",
    "48": "Pendeltåg 48 · Södertälje centrum–Gnesta",
    "7": "Spårväg City 7 · T-Centralen–Waldemarsudde",
    "12": "Nockebybanan 12 · Alvik–Nockeby",
    "21": "Lidingöbanan 21 · Ropsten–Gåshaga brygga",
    "30": "Tvärbanan 30 · Sickla–Solna station",
    "31": "Tvärbanan 31 · Alviks strand–Bromma flygplats",
    "27": "Roslagsbanan 27 · Stockholms östra–Kårsta",
    "28": "Roslagsbanan 28 · Stockholms östra–Österskär",
    "29": "Roslagsbanan 29 · Stockholms östra–Näsbypark",
    "25": "Saltsjöbanan 25 · Henriksdal–Saltsjöbaden",
    "26": "Saltsjöbanan 26 · Igelboda–Solsidan",
}

# 43X is an express variant of 43 and does not appear on SL's map, so it is
# folded into 43; it calls at no station 43 misses.
RAIL_LABELS = {
    "25": "25", "26": "26", "27": "27", "28": "28", "29": "29",
    "40": "40", "41": "41", "43": "43", "43X": "43", "48": "48",
}

# OSM tags individual platform tracks as stops; they are not stations
JUNK_NAME = re.compile(r"^Sp[åa]r\b|^Plattform")


def load(name):
    with open(os.path.join(RAW, name), encoding="utf-8") as fh:
        return json.load(fh)["elements"]


def metres(a, b):
    dy = (a[0] - b[0]) * 111_320.0
    dx = (a[1] - b[1]) * 111_320.0 * math.cos(math.radians(a[0]))
    return math.hypot(dx, dy)


def normalise(name):
    """Two OSM names for one station: 'Ulriksdal station', 'Stockholm Odenplan'."""
    key = name.casefold()
    key = re.sub(r"\s+station$", "", key)
    key = re.sub(r"^stockholms?\s+", "", key)
    return key


def kommun_name(raw):
    """'Stockholms kommun' -> 'Stockholm', but 'Upplands Väsby kommun' keeps its s."""
    name = re.sub(r"\s+kommun$", "", raw)
    if name.endswith("s") and " " not in name and "-" not in name:
        name = name[:-1]
    return name


# ---------------------------------------------------------------- sources

def metro_stops():
    """The 100 tunnelbana stations, with the lines that call there."""
    stops = {}
    for el in load("metro.json"):
        name = el["tags"].get("name")
        if name == "Rissne tunnelbanestation":
            continue  # duplicate node for Rissne
        stops[name] = {"lat": el["lat"], "lon": el["lon"], "lines": set(),
                       "nodes": {el["id"]}}

    node_tags = {e["id"]: e.get("tags", {}) for e in load("subnodes.json")}
    for rel in load("subrels.json"):
        label = rel["tags"]["ref"]
        for member in rel["members"]:
            if member["type"] != "node":
                continue
            name = node_tags.get(member["ref"], {}).get("name")
            if name in stops:
                stops[name]["lines"].add(label)

    # OSM's stop node for Hallonbergen carries no name, so it never matches above
    stops["Hallonbergen"]["lines"].add("10")
    return stops


def route_stops(rel_file, stop_file, label_for):
    """Stops on a set of route relations, one averaged point per name."""
    if stop_file:
        elements = {(e["type"], e["id"]): e for e in load(stop_file)}
        relations = load(rel_file)
    else:
        both = load(rel_file)
        elements = {(e["type"], e["id"]): e for e in both if e["type"] != "relation"}
        relations = [e for e in both if e["type"] == "relation"]

    stops = {}
    for rel in relations:
        label = label_for(rel["tags"]["ref"])
        for member in rel["members"]:
            if not member["role"].startswith(("stop", "platform")):
                continue
            el = elements.get((member["type"], member["ref"]))
            if not el:
                continue
            name = el.get("tags", {}).get("name")
            lat = el.get("lat") or el.get("center", {}).get("lat")
            lon = el.get("lon") or el.get("center", {}).get("lon")
            if not name or lat is None or JUNK_NAME.match(name):
                continue
            stop = stops.setdefault(name, {"pts": [], "lines": set(), "nodes": set()})
            stop["pts"].append((lat, lon))
            stop["lines"].add(label)
            if el["type"] == "node":
                stop["nodes"].add(el["id"])

    # each direction has its own stop node a few metres away; average them
    return {
        name: {
            "lat": sum(p[0] for p in s["pts"]) / len(s["pts"]),
            "lon": sum(p[1] for p in s["pts"]) / len(s["pts"]),
            "lines": s["lines"],
            "nodes": s["nodes"],
        }
        for name, s in stops.items()
    }


# ---------------------------------------------------------------- assembly

def build_rows(verbose=False):
    """One row per hiding-zone centre."""
    sources = [
        metro_stops(),
        route_stops("tram_rels.json", "tram_stops.json", lambda ref: ref),
        route_stops("rail_members.json", None, lambda ref: RAIL_LABELS[ref]),
    ]

    merged = []          # list of dicts, in first-seen order
    by_key = {}          # normalised name -> index into merged

    def absorb(index, stop):
        merged[index]["lines"] |= stop["lines"]
        merged[index]["nodes"] |= stop.get("nodes", set())

    for source in sources:
        for name, stop in sorted(source.items()):
            here = (stop["lat"], stop["lon"])
            key = normalise(name)
            hit = by_key.get(key)
            if hit is not None and metres(here, merged[hit]["pt"]) <= NAME_MERGE_M:
                absorb(hit, stop)
                continue

            # a stop this close on a *different* system is the same interchange;
            # two stops on the same system that happen to be close are not
            systems = {SYSTEM_OF[LINE_COLOURS[l]] for l in stop["lines"]}
            near = None
            for i, other in enumerate(merged):
                shares = systems & {SYSTEM_OF[LINE_COLOURS[l]] for l in other["lines"]}
                if not shares and metres(here, other["pt"]) <= NEAR_MERGE_M:
                    near = i
                    break
            if near is not None:
                if verbose:
                    print("  merged %-24s into %-24s (%3d m)"
                          % (name, merged[near]["name"], metres(here, merged[near]["pt"])))
                absorb(near, stop)
                by_key.setdefault(key, near)
                continue

            merged.append({"name": name, "pt": here, "lines": set(stop["lines"]),
                           "nodes": set(stop.get("nodes", set()))})
            by_key[key] = len(merged) - 1

    kommun_of = {int(k): kommun_name(v) for k, v in
                 json.load(open(os.path.join(RAW, "node_kommun.json"), encoding="utf-8")).items()}

    order = list(LINE_COLOURS)
    rows = []
    for stop in merged:
        lines = sorted(stop["lines"], key=order.index)  # SL map order
        colours, systems = [], []
        for line in lines:
            colour = LINE_COLOURS[line]
            if colour not in colours:
                colours.append(colour)
            if SYSTEM_OF[colour] not in systems:
                systems.append(SYSTEM_OF[colour])
        systems.sort(key=SYSTEM_ORDER.index)
        kommun = next((kommun_of[n] for n in sorted(stop["nodes"]) if n in kommun_of), "")
        rows.append({
            "name": stop["name"],
            "system": " + ".join(systems),
            "lines": "/".join(lines),
            "colour": "/".join(colours),
            "kommun": kommun,
            "lat": round(stop["pt"][0], 6),
            "lon": round(stop["pt"][1], 6),
        })
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def route_lines():
    """One entry per line: label, colour and the ways that draw it."""
    out = []
    for rel in load("route_geom.json") + load("rail_geom.json"):
        label = GEOM_LINES.get(rel["id"])
        if not label:
            continue
        ways = [m["geometry"] for m in rel["members"]
                if m["type"] == "way" and m.get("geometry") and not m["role"]]
        out.append({"label": label, "colour": LINE_COLOURS[label],
                    "name": LINE_NAMES[label], "ways": ways})
    out.sort(key=lambda r: list(LINE_COLOURS).index(r["label"]))
    return out


def circle(lat, lon, radius_m, points=48):
    ring = []
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(lat)))
    for i in range(points + 1):
        theta = 2 * math.pi * i / points
        ring.append((lon + dlon * math.cos(theta), lat + dlat * math.sin(theta)))
    return ring


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- KML

def styles_kml():
    parts = []
    for colour, kml in KML_COLOURS.items():
        parts.append(
            f'<Style id="line-{colour}"><LineStyle><color>{kml}</color><width>4</width></LineStyle></Style>'
            f'<Style id="dot-{colour}"><IconStyle><color>{kml}</color><scale>0.9</scale>'
            '<Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>'
            '</IconStyle></Style>'
        )
    parts.append('<Style id="zone"><LineStyle><color>ff0080ff</color><width>2</width></LineStyle>'
                 '<PolyStyle><color>260080ff</color></PolyStyle></Style>')
    parts.append('<Style id="border"><LineStyle><color>ff0000ff</color><width>3</width></LineStyle>'
                 '<PolyStyle><color>00000000</color></PolyStyle></Style>')
    return "".join(parts)


def lines_folder():
    parts = ["<Folder><name>Transit lines</name>"]
    for line in route_lines():
        geoms = "".join(
            "<LineString><tessellate>1</tessellate><coordinates>"
            + " ".join(f"{p['lon']:.6f},{p['lat']:.6f},0" for p in way)
            + "</coordinates></LineString>"
            for way in line["ways"]
        )
        parts.append("<Placemark>"
                     f"<name>{esc(line['name'])}</name>"
                     f"<styleUrl>#line-{line['colour']}</styleUrl>"
                     f"<MultiGeometry>{geoms}</MultiGeometry></Placemark>")
    parts.append("</Folder>")
    return "".join(parts)


def stops_folder(rows, nested=True):
    parts = ["<Folder><name>Stops</name>"] if nested else []
    for system in SYSTEM_ORDER:
        group = [r for r in rows if r["system"].split(" + ")[0] == system]
        if not group:
            continue
        parts.append(f"<Folder><name>{system}</name>")
        for row in group:
            parts.append("<Placemark>"
                         f"<name>{esc(row['name'])}</name>"
                         f"<description>{esc(row['lines'] + ' · ' + row['kommun'])}</description>"
                         f"<styleUrl>#dot-{row['colour'].split('/')[0]}</styleUrl>"
                         f"<Point><coordinates>{row['lon']},{row['lat']},0</coordinates></Point>"
                         "</Placemark>")
        parts.append("</Folder>")
    if nested:
        parts.append("</Folder>")
    return "".join(parts)


def zones_folder(rows):
    parts = [f"<Folder><name>Hiding zones ({ZONE_RADIUS_M} m)</name>"]
    for row in rows:
        ring = " ".join(f"{lon:.6f},{lat:.6f},0"
                        for lon, lat in circle(row["lat"], row["lon"], ZONE_RADIUS_M))
        parts.append("<Placemark>"
                     f"<name>{esc(row['name'])}</name><styleUrl>#zone</styleUrl>"
                     f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{ring}</coordinates>"
                     "</LinearRing></outerBoundaryIs></Polygon></Placemark>")
    parts.append("</Folder>")
    return "".join(parts)


def border_ring():
    return circle(BORDER_CENTRE[0], BORDER_CENTRE[1], BORDER_RADIUS_KM * 1000, points=360)


def border_folder():
    coords = " ".join(f"{lon:.5f},{lat:.5f},0" for lon, lat in border_ring())
    return ("<Folder><name>Game border</name>"
            "<Placemark><name>Game border</name><styleUrl>#border</styleUrl>"
            f"<Polygon><outerBoundaryIs><LinearRing><coordinates>{coords}</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon></Placemark></Folder>")


def kml_doc(title, body):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            f"<name>{esc(title)}</name>{styles_kml()}{body}</Document></kml>")


# ---------------------------------------------------------------- writers

def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(text)
    return name


def write_csv(rows):
    fields = ["name", "system", "lines", "colour", "kommun", "lat", "lon"]
    with open(os.path.join(OUT, "stations.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return "stations.csv"


def write_geojson(rows):
    features = [{
        "type": "Feature",
        "properties": {"name": r["name"], "system": r["system"], "lines": r["lines"],
                       "kommun": r["kommun"]},
        "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
    } for r in rows]
    for line in route_lines():
        features.append({
            "type": "Feature",
            "properties": {"name": line["name"], "line": line["label"]},
            "geometry": {"type": "MultiLineString", "coordinates": [
                [[p["lon"], p["lat"]] for p in way] for way in line["ways"]]},
        })
    features.append({
        "type": "Feature",
        "properties": {"name": "Game border"},
        "geometry": {"type": "Polygon",
                     "coordinates": [[[round(lon, 5), round(lat, 5)] for lon, lat in border_ring()]]},
    })
    with open(os.path.join(OUT, "stations.geojson"), "w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh,
                  ensure_ascii=False, indent=1)
    return "stations.geojson"


if __name__ == "__main__":
    rows = build_rows(verbose=True)

    counts = {}
    for row in rows:
        counts[row["system"]] = counts.get(row["system"], 0) + 1
    print(f"\n{len(rows)} hiding-zone centres")
    for system, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {system}")
    missing = [r["name"] for r in rows if not r["kommun"]]
    if missing:
        print("  no kommun for:", ", ".join(missing))

    far = max(rows, key=lambda r: metres((r["lat"], r["lon"]), BORDER_CENTRE))
    print(f"  border circle r={BORDER_RADIUS_KM} km, area "
          f"{math.pi * BORDER_RADIUS_KM ** 2:,.0f} km2; furthest stop "
          f"{metres((far['lat'], far['lon']), BORDER_CENTRE) / 1000:.1f} km ({far['name']})")

    written = [
        write_csv(rows),
        write_geojson(rows),
        write("all-layers.kml", kml_doc("Hide and Seek Stockholm",
              lines_folder() + stops_folder(rows) + zones_folder(rows) + border_folder())),
        write("transit-lines.kml", kml_doc("Transit lines", lines_folder())),
        write("stations.kml", kml_doc("Stops", stops_folder(rows, nested=False))),
        write("hiding-zones.kml", kml_doc("Hiding zones", zones_folder(rows))),
        write("border.kml", kml_doc("Game border", border_folder())),
    ]
    for name in written:
        print(f"wrote data/{name} ({os.path.getsize(os.path.join(OUT, name)) // 1024} KB)")
