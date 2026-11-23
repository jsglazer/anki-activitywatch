#!/bin/zsh
# Links this repo's add-on into Anki, so Anki runs the code straight from the repo. Restart Anki afterwards.
# Run on each Mac: scripts/install-dev.sh
set -euo pipefail
src="${0:A:h:h}/src/anki_activitywatch"
addons="$HOME/Library/Application Support/Anki2/addons21"
dest="$addons/anki_activitywatch"
if [[ ! -d "$addons" ]]; then
  echo "no Anki add-ons folder at $addons" >&2
  exit 1
fi
if [[ -e "$dest" && ! -L "$dest" ]]; then
  echo "$dest exists and is not a link; remove it first" >&2
  exit 1
fi
ln -sfn "$src" "$dest"
echo "linked $dest -> $src"
echo "Restart Anki, then check Tools → ActivityWatch status."
