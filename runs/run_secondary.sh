#!/bin/sh
# Secondary analysis declared in docs/analysis_plan.md: B1 and B2 with qwen3.5:9b, same prompts and evidence. Sealed.
set -e
cd "$(dirname "$0")/.."
for m in B1 B2; do
  .venv/Scripts/python.exe -X utf8 -m cipher.run --method $m --split evaluation --run-id secondary-v1-qwen35-9b-$m --model qwen3.5:9b
done
