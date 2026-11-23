# anki-activitywatch

[![release](https://img.shields.io/github/v/release/jsglazer/anki-activitywatch)](https://github.com/jsglazer/anki-activitywatch/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Built with Claude](https://img.shields.io/badge/Built%20with-Claude-D97757)](https://claude.com/claude-code)

Version 1.0.0

An Anki add-on that tells [ActivityWatch](https://activitywatch.net) which deck you are working in, as you work. Anki's window titles never name the deck ("User 1 - Anki", "Browse", "Add"), so the window watcher alone can't tell an Econ review session from a Calculus one. This add-on fills that gap for the Classes dashboard in [activity-watch](https://github.com/jsglazer/activity-watch).

## What it reports

Each heartbeat goes to the local ActivityWatch server, in the bucket `aw-watcher-anki-activity_<host>` (event type `app.anki.activity`), with data `{deck, activity}`. `<host>` is the host name ActivityWatch itself reports, so the bucket lines up with the window watcher on the same Mac.

| Focused window | `activity` | `deck` |
|---|---|---|
| Main window, reviewing | `review` | the deck of the card shown |
| Main window, deck overview | `overview` | the current deck |
| Main window, deck list | `decks` | the current (last selected) deck |
| Browse | `browse` | the deck of the selected cards; if they span decks, the most common one (ties: the name that sorts first); `null` with nothing selected |
| Add | `add` | the deck chosen in the Add window |
| Edit Current | `edit` | the deck of the card being edited |

A card borrowed by a filtered deck is reported in its home deck, since that is what names the class. Other Anki windows (preferences, statistics, card info) and Anki in the background report nothing, which ends the current event.

While nothing changes, a heartbeat goes out every 5 seconds, with `pulsetime` set to twice that, so ActivityWatch merges them into one event. A change (new card, new selection, another window, a deck switch) is sent at once: the old event is closed at that moment and the new one starts there.

The add-on never shows an error and never waits on the network: heartbeats go to a background thread through a small queue. If ActivityWatch isn't running, the add-on stops trying for 15 seconds, drops heartbeats meanwhile and tries again.

## Install

On each Mac, link the add-on from the repo into Anki and restart Anki:

```
git clone https://github.com/jsglazer/anki-activitywatch.git
anki-activitywatch/scripts/install-dev.sh
```

Or build `build/anki_activitywatch.ankiaddon` with `scripts/build.sh` and open it with Anki. Needs Anki 26.9.4 or later.

Then open **Tools → ActivityWatch status**: it shows the bucket, the last heartbeat ActivityWatch accepted, what is being reported now, and the last error.

## Config

Tools → Add-ons → ActivityWatch deck reporter → Config:

| Key | Default | Meaning |
|---|---|---|
| `enabled` | `true` | `false` stops reporting |
| `activitywatch_url` | `http://127.0.0.1:5600` | the local ActivityWatch server |
| `heartbeat_seconds` | `5` | how often to repeat the heartbeat while nothing changes (1 to 60) |

## Limits

- The experimental Svelte Add window (Shift-click Add) keeps its deck in the web view, so the add-on reports the current deck there instead.
- Reviews on AnkiMobile aren't seen. History from before the install stays with `scripts/aw-anki-import.py` in activity-watch.
- The add-on only reports decks; which deck belongs to which class is decided in activity-watch's `config/classes.json`.

## Development

```
uv sync
uv run pytest            # core, client and collection tests (headless)
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy src          # strict
scripts/build.sh         # build/anki_activitywatch.ankiaddon
```

| Path | Purpose |
|---|---|
| `src/anki_activitywatch/__init__.py` | entry point; registers the hooks |
| `src/anki_activitywatch/core/` | pure logic: `tracker.py` (when to send what), `decks.py` (most common deck), `aw.py` (ActivityWatch URLs and bodies), `settings.py` (config with defaults) |
| `src/anki_activitywatch/collection_ops.py` | deck names from the collection (home deck for filtered cards) |
| `src/anki_activitywatch/aw_client.py` | background sender: bucket creation, heartbeats, back-off, status |
| `src/anki_activitywatch/ui/` | Qt shell: which window has focus (`window_context.py`), timer, hooks and Tools menu (`addon.py`) |
| `tests/` | pytest; collection tests use a throwaway collection, never your profile |
| `scripts/build.sh`, `scripts/install-dev.sh` | package; link into Anki |

## License

MIT
