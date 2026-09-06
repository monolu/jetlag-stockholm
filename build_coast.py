"""
The coastline: a Google My Maps layer, and a drawn fallback.

Our coast ruling is the one thing a player cannot look up in Google Maps —
Mälaren and Saltsjön are painted the same blue — so it has to be drawn. The line
itself comes from OpenStreetMap's natural=coastline, which happens to run
exactly where our ruling does: OSM treats Mälaren as an inland lake and starts
the sea at the locks.

    data/coastline.kml  the layer to add to the My Map, at 10 m accuracy. This
                        is the one people use: it sits on Google's basemap and
                        pans and zooms like any other layer.
    figure()            the same shore drawn cold, for the Artifact copy, which
                        cannot load an iframe. Thinned to 50 m with the skerries
                        under 250 m across dropped, since at 100 m to the pixel
                        they are specks. Without a basemap under it, it is a
                        diagram of the ruling rather than a map.

Run: python build_coast.py
"""

import io
import json
import math
import os

import build_map as M

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, "data", "osm", "coastline.json")

LAT_M = 111320.0
LON_M = 111320.0 * math.cos(math.radians(M.BORDER_CENTRE[0]))

# The figure's frame: a 600 square with the border circle just inside it.
SIZE = 600
MID = SIZE / 2
RING = 285.0
SCALE = RING / (M.BORDER_RADIUS_KM * 1000)

SEA = "#2e8fd6"      # holds up on a white card and a navy one alike

# Where the ruling actually bites. Each is a lock, and the sea starts below it.
LOCKS = [
    (59.3203, 18.0715, "Slussen", "end"),
    (59.3040, 18.0975, "Hammarbyslussen", "start"),
    (59.1958, 17.6270, "Södertälje sluss", "start"),
]

# Named water. The blue line already says which counts, so the labels only have
# to be legible over it; the fresh ones are greyed to keep them out of the way.
# Riddarfjärden belongs here too, but its label lands on Slussen's.
WATER = [
    (59.355, 17.560, "Mälaren", False, "middle"),
    (59.330, 18.160, "Saltsjön", True, "middle"),
    (59.430, 18.330, "Trälhavet", True, "middle"),
    (59.155, 17.735, "Hallsfjärden", True, "middle"),
]


def project(lat, lon):
    return (MID + (lon - M.BORDER_CENTRE[1]) * LON_M * SCALE,
            MID - (lat - M.BORDER_CENTRE[0]) * LAT_M * SCALE)


def thin(points, tol):
    """Douglas-Peucker on (lat, lon) pairs, tolerance in metres."""
    if len(points) < 3:
        return points
    ax, ay = points[0][1] * LON_M, points[0][0] * LAT_M
    bx, by = points[-1][1] * LON_M, points[-1][0] * LAT_M
    dx, dy = bx - ax, by - ay
    span = math.hypot(dx, dy)
    worst, at = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i][1] * LON_M, points[i][0] * LAT_M
        if span == 0:
            far = math.hypot(px - ax, py - ay)
        else:
            far = abs(dy * px - dx * py + bx * ay - by * ax) / span
        if far > worst:
            worst, at = far, i
    if worst <= tol:
        return [points[0], points[-1]]
    return thin(points[:at + 1], tol)[:-1] + thin(points[at:], tol)


def across(run):
    """How wide the run is, corner to corner."""
    lats = [p[0] for p in run]
    lons = [p[1] for p in run]
    return math.hypot((max(lats) - min(lats)) * LAT_M, (max(lons) - min(lons)) * LON_M)


def runs():
    return json.load(io.open(SNAPSHOT, encoding="utf-8"))["runs"]


# ------------------------------------------------------------------ the labels

def label_box(x, y, text, size, anchor):
    """Roughly where a label's ink lands. Saira Condensed runs about .42em a
    character; .46 leaves room for the fallback font."""
    width = len(text) * size * 0.46
    left = {"start": x, "middle": x - width / 2, "end": x - width}[anchor]
    return (left, y - size * 0.75, left + width, y + size * 0.25)


def check(boxes):
    """Labels must sit inside the border and off each other."""
    problems = []
    for name, (x0, y0, x1, y1) in boxes:
        for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
            if math.hypot(cx - MID, cy - MID) > RING - 4:
                problems.append(f"{name} runs outside the border")
                break
    for i, (a, box_a) in enumerate(boxes):
        for b, box_b in boxes[i + 1:]:
            if (box_a[0] < box_b[2] and box_b[0] < box_a[2]
                    and box_a[1] < box_b[3] and box_b[1] < box_a[3]):
                problems.append(f"{a} overlaps {b}")
    return problems


# ------------------------------------------------------------------ the layer

def kml():
    body = ['<Style id="coast"><LineStyle><color>ffd68f2e</color><width>3</width>'
            "</LineStyle></Style>",
            "<Folder><name>Coastline</name>"]
    for run in runs():
        line = " ".join(f"{lon},{lat},0" for lat, lon in run)
        body.append("<Placemark><styleUrl>#coast</styleUrl><LineString>"
                    f"<tessellate>1</tessellate><coordinates>{line}</coordinates>"
                    "</LineString></Placemark>")
    body.append("</Folder>")
    doc = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           "<name>Coastline — the salt water</name>" + "".join(body) + "</Document></kml>")
    path = os.path.join(HERE, "data", "coastline.kml")
    io.open(path, "w", encoding="utf-8").write(doc)
    return path


# ------------------------------------------------------------------ the figure

def figure():
    paths = []
    kept = 0
    for run in runs():
        if across(run) < 250:
            continue
        thinned = thin(run, 50)
        if len(thinned) < 2:
            continue
        kept += 1
        xy = [project(lat, lon) for lat, lon in thinned]
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in xy)
        paths.append(d)

    boxes = []
    marks = []
    for lat, lon, name, anchor in LOCKS:
        x, y = project(lat, lon)
        tx = x + (9 if anchor == "start" else -9)
        ty = y + 4
        marks.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--ink)" '
                     'stroke="var(--surface)" stroke-width="2"/>')
        marks.append(f'<text class="mark" x="{tx:.1f}" y="{ty:.1f}" '
                     f'text-anchor="{anchor}">{name}</text>')
        boxes.append((name, label_box(tx, ty, name, 13, anchor)))

    names = []
    for lat, lon, name, salt, anchor in WATER:
        x, y = project(lat, lon)
        cls = "sea" if salt else "fresh"
        names.append(f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}" '
                     f'text-anchor="{anchor}">{name}</text>')
        boxes.append((name, label_box(x, y, name, 15, anchor)))

    # a scale bar, in the empty north-west where Mälaren has no coast to draw
    bar_x, bar_y, bar = 120.0, 180.0, 10000 * SCALE
    marks.append(f'<path d="M{bar_x} {bar_y - 5} L{bar_x} {bar_y + 5} M{bar_x} {bar_y} '
                 f'L{bar_x + bar:.1f} {bar_y} M{bar_x + bar:.1f} {bar_y - 5} '
                 f'L{bar_x + bar:.1f} {bar_y + 5}" stroke="var(--muted)" stroke-width="2" '
                 'fill="none"/>')
    marks.append(f'<text class="mark" x="{bar_x + bar / 2:.1f}" y="{bar_y - 10:.1f}" '
                 'text-anchor="middle">10 km</text>')
    boxes.append(("the scale label", label_box(bar_x + bar / 2, bar_y - 10, "10 km", 13, "middle")))
    boxes.append(("the scale bar", (bar_x, bar_y - 5, bar_x + bar, bar_y + 5)))

    problems = check(boxes)
    if problems:
        raise SystemExit("\n".join(problems))

    return (f'<svg viewBox="0 0 {SIZE} {SIZE}" role="img" '
            'aria-label="The salt water inside the border, which is what counts as coast">\n'
            f'  <circle cx="{MID}" cy="{MID}" r="{RING}" fill="var(--surface-2)" '
            'stroke="var(--rule-strong)" stroke-width="2" stroke-dasharray="7 6"/>\n'
            f'  <g fill="none" stroke="{SEA}" stroke-width="2.2" stroke-linecap="round" '
            'stroke-linejoin="round">\n    '
            + "\n    ".join(f'<path d="{d}"/>' for d in paths)
            + "\n  </g>\n  " + "\n  ".join(names) + "\n  " + "\n  ".join(marks)
            + "\n</svg>"), kept


if __name__ == "__main__":
    print(f"{len(runs())} coastline runs in the snapshot")
    path = kml()
    print(f"wrote {os.path.relpath(path, HERE)} "
          f"({os.path.getsize(path) / 1024:.0f} KB)")
    svg, kept = figure()
    print(f"figure: {kept} runs drawn, {len(svg) / 1024:.0f} KB of SVG")
