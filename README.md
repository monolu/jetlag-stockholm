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
**<https://monolu.github.io/jetlag-stockholm/>** — rules, local definitions, all 252
stops, and the network on a real map. Send that link to everyone.

The map section has two tabs. **Network** is our own data on Leaflet, lines in SL's
colours with a switch per system and a 500 m zone toggle. **Google** is our My Map,
<https://www.google.com/maps/d/viewer?mid=1KjLl3dy7DhmggT4o4qT-awV80zBs7t0>, for the
landmarks the questions ask about. The Google one is a cross-origin iframe, so its styling
and controls are Google's and cannot be changed from our side; that is why both are there.

It is built by `build_site.py` into `docs/`, from `field-manual.html`. There is also an
Artifact copy at
<https://claude.ai/code/artifact/1da46632-5022-4f36-bdde-65406e5bc907>; it holds the same
text but draws the map itself, because an Artifact can neither embed an iframe nor load
map tiles.

`map.html` is a fallback: the same network on OpenStreetMap, full screen, working from
disk with no Google and no server.

## The network

| System | Stops | Reaches |
|---|---|---|
| Tunnelbana T10–T19 | 100 | Hjulsta, Akalla, Norsborg, Mörby centrum, Skarpnäck, Hässelby strand |
| Pendeltåg 40 / 41 / 43 / 48 | 40 | Upplands Väsby, Rosersberg, Bro, Södertälje, Tungelsta |
| Trams 7 / 12 / 21 / 30 / 31 | 60 | Waldemarsudde, Nockeby, Gåshaga brygga, Sickla, Solna station, Bromma flygplats |
| Roslagsbanan 27 / 28 / 29 | 36 | Lindholmen, Österskär, Näsbypark |
| Saltsjöbanan 25 / 26 | 17 | Saltsjöbaden, Solsidan |

Sixteen stops serve more than one system, which leaves **235 hiding-zone centres** across
**19 kommuner**, all of them in Stockholms län. The far end of every branch — Uppsala C,
Arlanda, Märsta, Bålsta, Gnesta, Nynäshamn, Kårsta and their neighbours — falls outside
the border and is not in the game, so a plain SL ticket covers everything.

## Building the map

Go to <https://www.google.com/mymaps>, create a new map, and import
`data/all-layers.kml`. That one file holds the 21 lines drawn and coloured, all 235 stops
foldered by system, a 500 m circle around every stop, and the border. Share it with
everyone and open it once in the Google Maps app so it caches.

If My Maps flattens the folders into a single layer, import these four instead:

| File | Layer |
|---|---|
| `data/transit-lines.kml` | The lines, coloured by system |
| `data/stations.kml` | The 235 stops |
| `data/hiding-zones.kml` | 500 m circle around every stop |
| `data/border.kml` | The 28.7 km border circle |

## Files

| File | What it is |
|---|---|
| `field-manual.html` | The published page: rules, map, local definitions, every stop |
| `01-rules.md` | The rulebook digested, medium numbers baked in, plus what the expansion adds |
| `03-house-rules.md` | The long-form version of our local rulings, with per-curse notes |
| `04-checklist.md` | Night-before checklist and the round run sheet |
| `data/all-layers.kml` | **Import this one.** Lines + stops + zones + border |
| `data/stations.csv` | All 235 stops: name, system, lines, colour, style, kommun, coordinates. Colour a map by the **style** column — it holds one value per stop, nine in all. `colour` lists every colour a stop carries, which runs to 22 distinct values, and Google My Maps only styles 20 before dropping the rest into "Other". |
| `data/stations.geojson` | Everything, for any tool that eats GeoJSON |
| `build_map.py` | Regenerates every file in `data/` from the OSM snapshots in `data/osm/` |
| `build_pages.py` | Builds both copies of the page from `page-template.html` |
| `build_mapdata.py` | Thins the network into `data/map-data.json`, the payload the page's map draws |
| `build_site.py` | Builds `docs/index.html`, the hosted page with the Leaflet map |
| `build_webmap.py` | Builds `map.html`, the standalone full-screen map |
| `cards/` | Every card and every question as data, plus a deck builder. See `cards/README.md` |

Stop and route data from OpenStreetMap, © OpenStreetMap contributors, ODbL.
