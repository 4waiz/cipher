#!/bin/sh
# Held-out (evaluation split) runs of every arm, strictly one at a time so latencies are comparable.
# Predictions are written to runs/sealed/ (git-ignored) and the console shows only completion counts.
set -e
cd "$(dirname "$0")/.."
TAG=${1:-v1}
for m in B0 B1 B2 B1R; do
  .venv/Scripts/python.exe -X utf8 -m cipher.run --method $m --split evaluation --run-id heldout-$TAG-$m
done
.venv/Scripts/python.exe - "$TAG" <<'PY'
import json, sys
tag = sys.argv[1]
json.dump({m: f"heldout-{tag}-{m}" for m in ("B0", "B1", "B2", "B1R")},
          open("configs/heldout_runs.json", "w", newline="\n"), indent=1)
PY
