"""
Builds data/map-data.json: the network as flat metre coordinates, small enough to
embed in the field manual and draw as an interactive SVG.

Everything is projected onto a local plane centred on the border circle, so x is
metres east and y is metres south. Route geometry is thinned with Douglas-Peucker,
which drops the points a reader could never see.

Run: python build_mapdata.py
"""

import json
import math
import os

import build_map as M

HERE = os.path.dirname(os.path.abspath(__file__))
TOLERANCE_M = 60


def projector():
    lat0, lon0 = M.BORDER_CENTRE
    scale = 111_320.0
    east = scale * math.cos(math.radians(lat0))

    def project(lat, lon):
        return round((lon - lon0) * east), round(-(lat - lat0) * scale)
    return project


def thin(points, tolerance):
    """Douglas-Peucker. Keeps the shape, drops the filler."""
    if len(points) < 3:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx - ax, by - ay
    span = math.hypot(dx, dy)

    worst, index = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        if span == 0:
            gap = math.hypot(px - ax, py - ay)
        else:
            gap = abs(dy * px - dx * py + bx * ay - by * ax) / span
        if gap > worst:
            worst, index = gap, i

    if worst <= tolerance:
        return [points[0], points[-1]]
    return thin(points[:index + 1], tolerance)[:-1] + thin(points[index:], tolerance)


def build():
    project = projector()
    rows = M.build_rows()

    lines = []
    kept = dropped = 0
    for line in M.route_lines():
        paths = []
        for way in line["ways"]:
            points = [project(p["lat"], p["lon"]) for p in way]
            trimmed = [points[0]]
            for point in points[1:]:
                if point != trimmed[-1]:
                    trimmed.append(point)
            dropped += len(trimmed)
            if len(trimmed) < 2:
                continue
            simple = thin(trimmed, TOLERANCE_M)
            kept += len(simple)
            paths.append([c for point in simple for c in point])
        lines.append({"n": line["name"], "c": line["colour"], "l": line["label"],
                      "p": paths})

    stops = []
    for row in rows:
        x, y = project(row["lat"], row["lon"])
        stops.append([row["name"], row["lines"], row["kommun"],
                      row["system"].split(" + ")[0], x, y])

    doc = {
        "note": "x is metres east of the border centre, y is metres south.",
        "centre": list(M.BORDER_CENTRE),
        "radius": M.BORDER_RADIUS_KM * 1000,
        "zone": M.ZONE_RADIUS_M,
        "lines": lines,
        "stops": stops,
    }
    path = os.path.join(HERE, "data", "map-data.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(path)
    print(f"{len(lines)} lines, {len(stops)} stops")
    print(f"points {dropped} -> {kept} at {TOLERANCE_M} m tolerance")
    print(f"wrote data/map-data.json ({size / 1024:.0f} KB)")


if __name__ == "__main__":
    build()
