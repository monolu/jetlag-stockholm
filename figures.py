"""
The four question diagrams, built and checked.

Each is a map of the game: a circle, because our border is one. Every region
carries its own colour and its own label, so the picture says what the answer
rules out without the reader having to work it out. The layout follows the
rulebook's own diagrams at lifack.ch/docs/seeking.

Placing a label by eye inside a wedge or an annulus is how they end up half
outside it, so every label, dot and star here is checked against the region it
is meant to sit in before the SVG is written. Run this file to see the checks.
"""

import math

# ---------------------------------------------------------------- the frame

W, H = 380, 340          # viewBox
CX, CY, R = 190, 170, 132   # the play area: our 28.7 km border

# Region colours are fixed, not themed: white label text has to stay legible on
# them whether the card behind is white or navy.
NO = "#c0392b"       # the answer rules this ground out
YES = "#1e8449"      # the ground that is left
OUT = "#6b7280"      # out of range, so not an answer either way
PICK = "#d68910"     # the share the named thing keeps
REST = "#3b5bdb"     # the shares it does not

INK = "#111827"      # dots and stars, dark on every fill we use

STAR = ("M0 -13 L3.2 -4.4 L12.4 -4 L5.2 1.7 L7.6 10.5 L0 5.4 "
        "L-7.6 10.5 L-5.2 1.7 L-12.4 -4 L-3.2 -4.4 Z")


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def on_map(p):
    return dist(p, (CX, CY)) <= R - 2


# ------------------------------------------------------------- svg pieces

def star(x, y):
    return (f'  <g transform="translate({x} {y})"><path d="{STAR}" fill="{INK}" '
            'stroke="#fff" stroke-width="2.5" paint-order="stroke"/></g>')


def dot(x, y):
    return f'  <circle cx="{x}" cy="{y}" r="6" fill="{INK}" stroke="#fff" stroke-width="2"/>'


def label(x, y, lines, cls="area"):
    """Centred text. Two lines of an area label straddle y; one line sits on it."""
    top = y - 7 * (len(lines) - 1)
    rows = "".join(
        f'<tspan x="{x}" y="{round(top + 14 * i, 1)}">{line}</tspan>'
        for i, line in enumerate(lines))
    return f'  <text class="{cls}" x="{x}" y="{y}" text-anchor="middle">{rows}</text>'


def rule(x1, y1, x2, y2, colour="#fff", dash="5 4"):
    return (f'  <line x1="{round(x1, 1)}" y1="{round(y1, 1)}" x2="{round(x2, 1)}" '
            f'y2="{round(y2, 1)}" stroke="{colour}" stroke-width="2" stroke-dasharray="{dash}"/>')


# The circle sits at 58..322 by 38..302, so the box is cropped to it: the full
# 380 by 340 would spend a third of the card on margin.
def svg(title, body, tall=False):
    view = "40 20 300 322" if tall else "40 20 300 300"
    return (f'<svg viewBox="{view}" role="img" aria-label="{title}">\n'
            + "\n".join(body) + "\n"
            f'  <circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="var(--ink)" '
            'stroke-width="2.5"/>\n</svg>')


def clip(name):
    return f'  <clipPath id="{name}"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>'


# The width of a label, near enough. Saira Condensed at 12px runs about 5.6px an
# uppercase character; 6.4 leaves room for a fallback font.
def box(x, y, lines, per=6.4, lead=14):
    half = max(len(line) for line in lines) * per / 2
    top = y - 7 * (len(lines) - 1) - 10
    bottom = y + 7 * (len(lines) - 1) + 4
    return [(x - half, top), (x + half, top), (x - half, bottom), (x + half, bottom)]


PROBLEMS = []


def check(figure, what, points, inside):
    for p in points:
        if not on_map(p):
            PROBLEMS.append(f"{figure}: {what} at {p[0]:.0f},{p[1]:.0f} runs off the map")
        elif not inside(p):
            PROBLEMS.append(f"{figure}: {what} at {p[0]:.0f},{p[1]:.0f} is in the wrong region")


# ------------------------------------------------------- 1. matching

# Two museums; the bisector between them splits the map. The seekers stand by
# the eastern one, so only ground nearer to that one can answer yes.
M1, M2, S1 = (120, 110), (262, 205), (245, 248)
_mid = ((M1[0] + M2[0]) / 2, (M1[1] + M2[1]) / 2)
_d = (M2[0] - M1[0], M2[1] - M1[1])
_len = math.hypot(*_d)
_perp = (-_d[1] / _len, _d[0] / _len)
A = (_mid[0] + 400 * _perp[0], _mid[1] + 400 * _perp[1])
B = (_mid[0] - 400 * _perp[0], _mid[1] - 400 * _perp[1])


def _side(p):
    return ((p[0] - A[0]) * (B[1] - A[1]) - (p[1] - A[1]) * (B[0] - A[0]))


_yes_side = _side(S1) < 0


def near_m2(p):
    return (_side(p) < 0) == _yes_side


def near_m1(p):
    return not near_m2(p)


def matching():
    far = 200
    yes = (f"M{A[0]:.1f} {A[1]:.1f} L{B[0]:.1f} {B[1]:.1f} "
           f"L{B[0] + far:.1f} {B[1]:.1f} L{A[0] + far:.1f} {A[1]:.1f} Z")
    no = (f"M{A[0]:.1f} {A[1]:.1f} L{B[0]:.1f} {B[1]:.1f} "
          f"L{B[0] - far:.1f} {B[1]:.1f} L{A[0] - far:.1f} {A[1]:.1f} Z")

    check("matching", "no label", box(112, 186, ["POTENTIAL", "HIDER AREA", "IF NO"]), near_m1)
    check("matching", "yes label", box(262, 146, ["POTENTIAL", "HIDER AREA", "IF YES"]), near_m2)
    check("matching", "museum 1", box(120, 131, ["Museum #1"]), near_m1)
    check("matching", "museum 2", box(262, 226, ["Museum #2"]), near_m2)
    check("matching", "seekers", box(245, 270, ["SEEKERS"]), near_m2)

    return svg("Matching keeps the ground nearest the same museum as the seekers", [
        clip("clip-match"),
        '  <g clip-path="url(#clip-match)">',
        f'    <path d="{no}" fill="{NO}"/>',
        f'    <path d="{yes}" fill="{YES}"/>',
        f'    <line x1="{A[0]:.1f}" y1="{A[1]:.1f}" x2="{B[0]:.1f}" y2="{B[1]:.1f}" '
        'stroke="#fff" stroke-width="2.5" stroke-dasharray="7 5"/>',
        "  </g>",
        label(112, 186, ["POTENTIAL", "HIDER AREA", "IF NO"]),
        label(262, 146, ["POTENTIAL", "HIDER AREA", "IF YES"]),
        dot(*M1), label(120, 131, ["Museum #1"], "pin"),
        dot(*M2), label(262, 226, ["Museum #2"], "pin"),
        star(*S1), label(245, 270, ["SEEKERS"], "pin"),
    ])


# ------------------------------------------------------ 2. measuring

# One thing, and a circle drawn on it through the seekers. Inside that circle is
# closer to the thing than the seekers are.
G, S2 = (185, 155), (245, 130)
RG = dist(G, S2)


def closer(p):
    return dist(p, G) < RG - 3


def further(p):
    return dist(p, G) > RG + 3


def measuring():
    check("measuring", "closer label", box(185, 130, ["HIDER AREA", "IF CLOSER"]), closer)
    check("measuring", "further label", box(150, 255, ["POTENTIAL", "HIDER AREA", "IF FURTHER"]), further)
    check("measuring", "gröna lund", box(185, 179, ["Grona Lund"]), closer)
    check("measuring", "seekers", box(274, 117, ["SEEKERS"]), further)

    return svg("Measuring cuts at the seekers' own distance from the thing", [
        clip("clip-meas"),
        '  <g clip-path="url(#clip-meas)">',
        f'    <circle cx="{CX}" cy="{CY}" r="{R}" fill="{NO}"/>',
        f'    <circle cx="{G[0]}" cy="{G[1]}" r="{RG:.1f}" fill="{YES}" '
        'stroke="#fff" stroke-width="2.5" stroke-dasharray="7 5"/>',
        "  </g>",
        rule(G[0], G[1], S2[0], S2[1]),
        label(185, 130, ["HIDER AREA", "IF CLOSER"]),
        label(150, 255, ["POTENTIAL", "HIDER AREA", "IF FURTHER"]),
        dot(*G), label(185, 179, ["Gröna Lund"], "pin"),
        star(*S2), label(274, 117, ["SEEKERS"], "pin"),
    ])


# ---------------------------------------------------------- 3. radar

S3, RR = (205, 190), 62


def within(p):
    return dist(p, S3) < RR - 4


def beyond(p):
    return dist(p, S3) > RR + 4


def radar():
    check("radar", "hit label", box(205, 166, ["HIDER AREA", "IF HIT"]), within)
    check("radar", "miss label", box(138, 102, ["POTENTIAL", "HIDER AREA", "IF MISS"]), beyond)
    check("radar", "seekers", box(205, 216, ["SEEKERS"]), within)
    check("radar", "5 km", box(238, 182, ["5 km"]), within)

    return svg("Radar draws a circle of the asked size around the seekers", [
        clip("clip-radar"),
        '  <g clip-path="url(#clip-radar)">',
        f'    <circle cx="{CX}" cy="{CY}" r="{R}" fill="{NO}"/>',
        f'    <circle cx="{S3[0]}" cy="{S3[1]}" r="{RR}" fill="{YES}" '
        'stroke="#fff" stroke-width="2.5" stroke-dasharray="7 5"/>',
        "  </g>",
        label(138, 102, ["POTENTIAL", "HIDER AREA", "IF MISS"]),
        label(205, 166, ["HIDER AREA", "IF HIT"]),
        rule(S3[0], S3[1], S3[0] + RR, S3[1]),
        label(238, 182, ["5 km"], "pin"),
        star(*S3), label(205, 216, ["SEEKERS"], "pin"),
    ])


# ------------------------------------------------------ 4. tentacles

# Three museums inside a 2 km reach. The reach divides between them along the
# bisectors, which all meet at one point, so the three shares are true wedges.
S4, RT = (190, 145), 92
T1, T2, T3 = (136, 124), (244, 114), (186, 199)


def _circumcentre(a, b, c):
    d = 2 * (a[0] * (b[1] - c[1]) + b[0] * (c[1] - a[1]) + c[0] * (a[1] - b[1]))
    ux = ((a[0] ** 2 + a[1] ** 2) * (b[1] - c[1]) + (b[0] ** 2 + b[1] ** 2) * (c[1] - a[1])
          + (c[0] ** 2 + c[1] ** 2) * (a[1] - b[1])) / d
    uy = ((a[0] ** 2 + a[1] ** 2) * (c[0] - b[0]) + (b[0] ** 2 + b[1] ** 2) * (a[0] - c[0])
          + (c[0] ** 2 + c[1] ** 2) * (b[0] - a[0])) / d
    return (ux, uy)


C4 = _circumcentre(T1, T2, T3)


def _to_edge(direction):
    """From the meeting point, out along a bisector to the edge of the reach."""
    ax, ay = C4[0] - S4[0], C4[1] - S4[1]
    dotp = ax * direction[0] + ay * direction[1]
    t = -dotp + math.sqrt(dotp ** 2 + RT ** 2 - (ax ** 2 + ay ** 2))
    return (C4[0] + t * direction[0], C4[1] + t * direction[1])


def _bisector(a, b, away_from):
    """The half of a|b's bisector that runs away from the third museum."""
    mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    d = (b[0] - a[0], b[1] - a[1])
    n = math.hypot(*d)
    perp = (-d[1] / n, d[0] / n)
    if (away_from[0] - mid[0]) * perp[0] + (away_from[1] - mid[1]) * perp[1] > 0:
        perp = (-perp[0], -perp[1])
    return _to_edge(perp)


E12 = _bisector(T1, T2, T3)
E13 = _bisector(T1, T3, T2)
E23 = _bisector(T2, T3, T1)


def _angle(p):
    return math.degrees(math.atan2(p[1] - S4[1], p[0] - S4[0])) % 360


def _wedge(start, end):
    return (f"M{C4[0]:.1f} {C4[1]:.1f} L{start[0]:.1f} {start[1]:.1f} "
            f"A{RT} {RT} 0 0 1 {end[0]:.1f} {end[1]:.1f} Z")


def _in_wedge(start, end):
    lo, hi = _angle(start), _angle(end)
    span = (hi - lo) % 360

    def test(p):
        if dist(p, S4) > RT - 4:
            return False
        return ((_angle(p) - lo) % 360) < span
    return test


def out_of_reach(p):
    return dist(p, S4) > RT + 4


def tentacles():
    nearest_1 = _in_wedge(E13, E12)
    nearest_2 = _in_wedge(E12, E23)
    nearest_3 = _in_wedge(E23, E13)

    check("tentacles", "museum 1", box(136, 146, ["Museum #1"], per=6.0), nearest_1)
    check("tentacles", "museum 2", box(244, 136, ["Museum #2"], per=6.0), nearest_2)
    check("tentacles", "museum 3", box(186, 221, ["Museum #3"], per=6.0), nearest_3)
    check("tentacles", "out of reach", box(140, 262, ["OUT OF REACH"], per=6.0), out_of_reach)
    check("tentacles", "2 km", box(150, 106, ["2 km"]), nearest_1)
    check("tentacles", "callout arrow", [(176, 214)], nearest_3)

    return svg("A tentacle question leaves the share of the reach nearest one museum", [
        clip("clip-tent"),
        '  <g clip-path="url(#clip-tent)">',
        f'    <circle cx="{CX}" cy="{CY}" r="{R}" fill="{OUT}"/>',
        "  </g>",
        f'  <path d="{_wedge(E13, E12)}" fill="{REST}"/>',
        f'  <path d="{_wedge(E12, E23)}" fill="{REST}"/>',
        f'  <path d="{_wedge(E23, E13)}" fill="{PICK}"/>',
        f'  <circle cx="{S4[0]}" cy="{S4[1]}" r="{RT}" fill="none" stroke="#fff" '
        'stroke-width="2.5" stroke-dasharray="7 5"/>',
        f'  <g stroke="#fff" stroke-width="2" stroke-dasharray="5 4">',
        f'    <line x1="{C4[0]:.1f}" y1="{C4[1]:.1f}" x2="{E12[0]:.1f}" y2="{E12[1]:.1f}"/>',
        f'    <line x1="{C4[0]:.1f}" y1="{C4[1]:.1f}" x2="{E13[0]:.1f}" y2="{E13[1]:.1f}"/>',
        f'    <line x1="{C4[0]:.1f}" y1="{C4[1]:.1f}" x2="{E23[0]:.1f}" y2="{E23[1]:.1f}"/>',
        "  </g>",
        rule(S4[0], S4[1], S4[0] - RT * 0.94, S4[1] - RT * 0.34),
        label(150, 106, ["2 km"], "pin"),
        dot(*T1), label(136, 146, ["Museum #1"], "pin"),
        dot(*T2), label(244, 136, ["Museum #2"], "pin"),
        dot(*T3), label(186, 221, ["Museum #3"], "pin"),
        label(140, 262, ["OUT OF REACH"]),
        star(*S4),
        '  <path d="M190 314 L176 214" stroke="var(--ink)" stroke-width="2" fill="none"/>',
        '  <path d="M176 214 l-1 11 l8 -6 z" fill="var(--ink)"/>',
        label(190, 330, ["THE SHARE LEFT IF THEY SAY MUSEUM #3"], "out"),
    ], tall=True)


QUESTIONS = {
    "FIG-MATCHING": "Is your nearest museum the same as my nearest museum?",
    "FIG-MEASURING": "Compared to me, are you closer to or further from Gröna Lund?",
    "FIG-RADAR": "Are you within 5 km of me?",
    "FIG-TENTACLE": "Of the museums within 2 km of me, which are you nearest to?",
}


def build():
    figures = {
        "FIG-MATCHING": matching(),
        "FIG-MEASURING": measuring(),
        "FIG-RADAR": radar(),
        "FIG-TENTACLE": tentacles(),
    }
    if PROBLEMS:
        raise SystemExit("\n".join(PROBLEMS))
    return figures


if __name__ == "__main__":
    build()
    print("four figures, every label inside the region it names")
