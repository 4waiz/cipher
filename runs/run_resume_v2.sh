#!/bin/sh
# Resume the v2 held-out runs after the 17:29-19:19 sleep (runs skip cases already in predictions.jsonl).
# Each segment records the Ollama runtime version first, because Ollama auto-updated 0.40.6 -> 0.40.7 at 19:20.
set -e
cd "$(dirname "$0")/.."
seg() {  # $1 run-id, rest: cipher.run arguments
  printf '{"run_id": "%s", "segment_start": "%s", "ollama": %s}\n' "$1" "$(date -u +%FT%TZ)" "$(curl -s http://localhost:11434/api/version)" >> runs/sealed/runtime_versions.jsonl
  shift; .venv/Scripts/python.exe -X utf8 -m cipher.run "$@"
}
seg heldout-v2-B2 --method B2 --split evaluation --run-id heldout-v2-B2
seg heldout-v2-B1R --method B1R --split evaluation --run-id heldout-v2-B1R
.venv/Scripts/python.exe -c "import json; json.dump({m: f'heldout-v2-{m}' for m in ('B0', 'B1', 'B2', 'B1R')}, open('configs/heldout_runs.json', 'w', newline=chr(10)), indent=1)"
seg secondary-v2-qwen35-9b-B1 --method B1 --split evaluation --run-id secondary-v2-qwen35-9b-B1 --model qwen3.5:9b
seg secondary-v2-qwen35-9b-B2 --method B2 --split evaluation --run-id secondary-v2-qwen35-9b-B2 --model qwen3.5:9b
.venv/Scripts/python.exe -c "import json; json.dump({m: f'secondary-v2-qwen35-9b-{m}' for m in ('B1', 'B2')}, open('configs/secondary_runs.json', 'w', newline=chr(10)), indent=1)"
echo ALL_RUNS_FINISHED
