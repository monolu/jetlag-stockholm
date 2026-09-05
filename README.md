# Hide and Seek: Stockholm

A home game of **Jet Lag: The Game — Hide and Seek**, played across the whole SL rail
network: tunnelbana, pendeltåg, trams, Roslagsbanan and Saltsjöbanan. Six players, two
teams of three, and a hundred-card deck with every curse in play.

Rules sources: the community rulebook at <https://www.lifack.ch/docs/quick_start_guide>
for the base game, and the official expansion reference at
<https://rules.jetlagthegame.com/expansion/>. Neither is affiliated with Jet Lag / Nebula
/ Wendover.

## The setup in one breath

| | |
|---|---|
| Players | 2 teams of 3. Each team hides once. Longest single run wins. |
| Game size | **Medium**: 235 stops, 2,588 km² — 999 sq mi, inside the 1,000 a medium game allows |
| Transit in play | Every SL rail line. No buses, no ferries, nothing else. |
| Hiding zone | **500 m** radius around your chosen stop |
| Hiding period | **60 minutes** |
| Answer windows | 5 min for everything, 10 min for photo questions |
| Hours | 09:00–18:00, carrying into the next day if a round is still running |
| Border | A circle, radius **28.7 km**, centred 59.35 N / 17.92 E (`data/border.kml`) |
| Deck | 100 cards: 45 time bonuses (6 of them per cent cards), 25 powerups, 30 curses. Every curse legal. |

## The page

Everything you need during the game is one page, live at
**<https://monolu.github.io/jetlag-stockholm/>** — the map, the rules that differ here,
what counts as what, and all 235 stops. Send that link to everyone.

The map on it is our Google My Map,
<https://www.google.com/maps/d/viewer?mid=1KjLl3dy7DhmggT4o4qT-awV80zBs7t0>, embedded.
Google's basemap carries the landmarks the questions ask about, and Google Maps is our
source of truth, so there is no second map to reconcile with it.

`build_pages.py` builds the page from `page-template.html` into `docs/`, and writes an
Artifact copy, `field-manual.html`, at the same time. That copy holds the same text but
links to the map instead of embedding it, because an Artifact cannot load an iframe.

## The network

| System | Stops | Reaches |
|---|---|---|
| Tunnelbana 10–19 | 100 | Hjulsta, Akalla, Norsborg, Mörby centrum, Skarpnäck, Hässelby strand |
| Pendeltåg 40 / 41 / 43 / 48 | 40 | Upplands Väsby, Rosersberg, Bro, Södertälje syd, Tungelsta |
| Trams 7 / 12 / 21 / 30 / 31 | 60 | Waldemarsudde, Nockeby, Gåshaga brygga, Sickla, Solna station, Bromma flygplats |
| Roslagsbanan 27 / 28 / 29 | 36 | Lindholmen, Österskär, Näsbypark |
| Saltsjöbanan 25 / 26 | 17 | Saltsjöbaden, Solsidan |

Sixteen stops serve more than one system, which leaves **235 hiding-zone centres** across
**19 kommuner**, all of them in Stockholms län. The far end of every branch — Uppsala C,
Arlanda, Märsta, Bålsta, Gnesta, Nynäshamn, Kårsta and their neighbours — falls outside
the border and is not in the game, so a plain SL ticket covers everything.

## Building the map

Go to <https://www.google.com/mymaps>, create a new map, and import
`data/all-layers.kml`. That one file holds six layers: the 21 lines drawn and coloured,
all 235 stops foldered by system, the 500 m hiding zone around every stop, the 750 m and
250 m circles the two zone curses make, and the border. Share it with everyone and open it
once in the Google Maps app so it caches.

If My Maps flattens the folders into a single layer, import these four instead:

| File | Layer |
|---|---|
| `data/transit-lines.kml` | The lines, coloured by system |
| `data/stations.kml` | The 235 stops |
| `data/hiding-zones.kml` | The 500 m, 750 m and 250 m circles around every stop |
| `data/border.kml` | The 28.7 km border circle |

## Files

| File | What it is |
|---|---|
| `page-template.html` | The page itself. Both copies are built from it |
| `docs/index.html` | The hosted page, built. Do not edit it by hand |
| `01-rules.md` | The rulebook digested, medium numbers baked in, plus what the expansion adds |
| `03-house-rules.md` | The long-form version of our local rulings, with per-curse notes |
| `04-checklist.md` | Night-before checklist and the round run sheet |
| `data/all-layers.kml` | **Import this one.** Lines + stops + zones + border |
| `data/stations.csv` | All 235 stops: name, system, lines, colour, style, kommun, coordinates. Colour a map by the **style** column — it holds one value per stop, nine in all. `colour` lists every colour a stop carries, which runs to 22 distinct values, and Google My Maps only styles 20 before dropping the rest into "Other". |
| `data/stations.geojson` | Everything, for any tool that eats GeoJSON |
| `build_map.py` | Regenerates every file in `data/` from the OSM snapshots in `data/osm/` |
| `build_pages.py` | Builds both copies of the page from `page-template.html` |
| `cards/` | Every card and every question as data, plus a deck builder. See `cards/README.md` |

Stop and route data from OpenStreetMap, © OpenStreetMap contributors, ODbL.
