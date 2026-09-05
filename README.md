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
| Game size | **Medium** settings on a large map: 252 stops, ~9,500 km² |
| Transit in play | Every SL rail line. No buses, no ferries, nothing else. |
| Hiding zone | **400 m** radius around your chosen stop |
| Hiding period | **60 minutes** |
| Answer windows | 5 min for everything, 10 min for photo questions |
| Hours | 09:00–18:00, carrying into the next day if a round is still running |
| Border | A circle, radius **55 km**, centred 59.38 N / 17.79 E (`data/border.kml`) |
| Deck | 100 cards: 45 time bonuses (6 of them per cent cards), 25 powerups, 30 curses. Every curse legal. |

## The page

Everything you need during the game is published as one page:
**<https://claude.ai/code/artifact/1da46632-5022-4f36-bdde-65406e5bc907>**
(private until you share it from the page's share menu). Source is `field-manual.html`,
and it is the authoritative version of the rules below.

## The network

| System | Stops | Reaches |
|---|---|---|
| Tunnelbana T10–T19 | 100 | Hjulsta, Akalla, Norsborg, Mörby centrum, Skarpnäck, Hässelby strand |
| Pendeltåg 40 / 41 / 43 / 43X / 48 | 54 | Uppsala C, Arlanda, Märsta, Bålsta, Nynäshamn, Gnesta |
| Trams 7 / 12 / 21 / 30 / 31 | 60 | Waldemarsudde, Nockeby, Gåshaga brygga, Sickla, Solna station, Bromma flygplats |
| Roslagsbanan 27 / 28 / 29 | 39 | Kårsta, Österskär, Näsbypark |
| Saltsjöbanan 25 / 26 | 17 | Saltsjöbaden, Solsidan |

Sixteen stops serve more than one system, which leaves **252 hiding-zone centres** across
**24 kommuner** and three län.

## Building the map

Go to <https://www.google.com/mymaps>, create a new map, and import
`data/all-layers.kml`. That one file holds the 21 lines drawn and coloured, all 252 stops
foldered by system, a 400 m circle around every stop, and the border. Share it with
everyone and open it once in the Google Maps app so it caches.

If My Maps flattens the folders into a single layer, import these four instead:

| File | Layer |
|---|---|
| `data/transit-lines.kml` | The lines, coloured by system |
| `data/stations.kml` | The 252 stops |
| `data/hiding-zones.kml` | 400 m circle around every stop |
| `data/border.kml` | The 55 km border circle |

## Files

| File | What it is |
|---|---|
| `field-manual.html` | The published page: rules, map, local definitions, every stop |
| `01-rules.md` | The rulebook digested, medium numbers baked in, plus what the expansion adds |
| `03-house-rules.md` | The long-form version of our local rulings, with per-curse notes |
| `04-checklist.md` | Night-before checklist and the round run sheet |
| `data/all-layers.kml` | **Import this one.** Lines + stops + zones + border |
| `data/stations.csv` | All 252 stops: name, system, lines, kommun, coordinates |
| `data/stations.geojson` | Everything, for any tool that eats GeoJSON |
| `build_map.py` | Regenerates every file in `data/` from the OSM snapshots in `data/osm/` |
| `build_mapdata.py` | Thins the network into `data/map-data.json`, the payload the page's map draws |
| `cards/` | Every card and every question as data, plus a deck builder. See `cards/README.md` |

Stop and route data from OpenStreetMap, © OpenStreetMap contributors, ODbL.
