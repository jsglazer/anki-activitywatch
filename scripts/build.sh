#!/bin/zsh
# Packages src/anki_activitywatch into build/anki_activitywatch.ankiaddon (a zip with the add-on files at its root).
set -euo pipefail
cd "${0:A:h}/.."
version=$(sed -n 's/^version = "\(.*\)"/\1/p' pyproject.toml | head -1)
manifest=$(python3 -c 'import json; print(json.load(open("src/anki_activitywatch/manifest.json"))["human_version"])')
if [[ "$version" != "$manifest" ]]; then
  echo "version mismatch: pyproject.toml $version, manifest.json $manifest" >&2
  exit 1
fi
mkdir -p build
out="$PWD/build/anki_activitywatch.ankiaddon"
rm -f "$out"
(cd src/anki_activitywatch && zip -qr "$out" . -x '*__pycache__*' -x 'meta.json' -x 'user_files/*' -x '.DS_Store')
echo "built $out ($version)"
