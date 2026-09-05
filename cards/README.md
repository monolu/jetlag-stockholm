# The cards

Every card in Hide and Seek, base game plus Expansion Pack Volume 1, as data.

| File | What it is |
|---|---|
| `cards.json` | All 180 cards, 94 distinct. The database. |
| `questions.json` | All 81 questions, six categories, with costs and size gates |
| `deck-stockholm.json` | The deck in our box: 45 time bonuses, 25 powerups, 30 curses |
| `deck.json` | A generated deck at the 50 / 25 / 25 target |
| `build_cards.py` | Rebuilds `cards.json` from `source/` |
| `build_questions.py` | Rebuilds `questions.json` from `source/questions/` |
| `build_deck.py` | Builds a deck, or checks one |
| `source/curses.csv` | Curse text, exported from the community card spreadsheet |
| `source/composition.csv` | Official card counts, same spreadsheet |

## What's in the printed sets

| | Base | Expansion 1 | Total |
|---|---|---|---|
| Time bonuses | 55 | 12 | 67 |
| Time traps | — | 5 | 5 |
| Powerups | 21 | 8 | 29 |
| Nothing | — | 5 | 5 |
| Curses | 24 | 50 | 74 |
| **Total** | **100** | **80** | **180** |

Time bonuses come in six colours, each carrying three values, one per game size:
red 2/3/5, orange 4/6/10, yellow 6/9/15, green 8/12/20, blue 12/18/30, black
20/36/60. The expansion adds four 5% and four 10% cards, worth a share of the hiding
time itself.

## Card shape

```json
{
  "id": "curse-jammed-door",
  "type": "curse",
  "set": "base",
  "name": "Curse Of The Jammed Door",
  "copies": 1,
  "text": "For the next [S0.5, M1, L3] hours, whenever the seekers want to pass …",
  "casting_cost": "Discard two cards.",
  "notes": "Seekers must roll two d6 dice. Dice can only be rolled to enter …",
  "sizes": [{"small": 0.5, "medium": 1, "large": 3}, {"small": 5, "medium": 10, "large": 15}],
  "text_medium": "For the next 1 hours, whenever the seekers want to pass …"
}
```

- `type` is `time_bonus`, `time_trap`, `powerup`, `nothing` or `curse`.
- `set` is `base` or `expansion-1`.
- `copies` is how many of that card the printed sets hold, not how many are in a deck.
- Card text carries `[S…, M…, L…]` triples, one value per game size. `sizes` lists them
  in order of appearance; `text_medium` and `casting_cost_medium` resolve them for a
  medium game, which is what we play.
- `notes` is the rulebook clarification for that card, or null.

## Building a deck

A deck is a subset of the 180. The target mix is 50% time bonuses, 25% curses and
25% powerups.

```bash
python build_deck.py                       # 100 cards, seed 1
python build_deck.py --size 120 --seed 7
python build_deck.py --check deck-stockholm.json
```

Time traps count towards the time share and Nothing cards towards the powerups. Within
each share, cards are drawn in proportion to how many the printed sets contain, so the
deck keeps the shape of the real one: plenty of red, a single Move. Curses are drawn at
random, one copy each.

`deck-stockholm.json` sits at 45 / 30 / 25 rather than 50 / 25 / 25 — five curses over
and five time bonuses under.

## Where this came from

Curse text and the card counts are from the community card spreadsheet
[here](https://docs.google.com/spreadsheets/d/1ZigDKsSCDxbp0JDWTnt0OGOlfxNEqICA3FnXy46p1Jk),
originally by u/Jim777PS3 and adapted for the expansion by @d\_ph. Time bonus and powerup
wording is transcribed from the physical cards. Jet Lag: The Game is by Nebula and
Wendover Productions; none of this is affiliated with them.

## The questions

`questions.json` holds the investigation book: 81 questions across six categories.

| Category | Questions | In a medium game | Cost | Answer |
|---|---|---|---|---|
| Matching | 20 | 20 | draw 3, keep 1 | 5 min |
| Measuring | 21 | 21 | draw 3, keep 1 | 5 min |
| Thermometer | 4 | 3 | draw 2, keep 1 | 5 min |
| Radar | 10 | 10 | draw 2, keep 1 | 5 min |
| Photo | 18 | 14 | draw 1, keep 1 | 10 min |
| Tentacles | 8 | 4 | draw 4, keep 2 | 5 min |

Each question carries the sizes it is available in, so filtering to `medium` gives the 72
we can actually ask. Matching and measuring questions carry the rulebook's group
(transit, borders, natural, places of interest, public utilities); radar, thermometer and
tentacle questions carry a distance in both miles and metres; photo questions carry their
framing requirements.
