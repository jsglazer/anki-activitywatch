- `enabled` — `true` to report to ActivityWatch, `false` to stop.
- `activitywatch_url` — the local ActivityWatch server. The default is `http://127.0.0.1:5600`.
- `heartbeat_seconds` — how often to repeat the heartbeat while nothing changes, from 1 to 60. The default is 5. Changes (a new card, a new selection, another window) are sent at once.

Data goes to the bucket `aw-watcher-anki-activity_<host>` as `{deck, activity}`, with activity one of `review`, `browse`, `add`, `edit`, `overview`, `decks`. Tools → ActivityWatch status shows the last heartbeat and any error.
