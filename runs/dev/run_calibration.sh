#!/bin/sh
# Calibration-split runs of every arm (development only; never scored as held-out data).
set -e
cd "$(dirname "$0")/../.."
while pgrep -f "cipher.run --method B1R --split practice" >/dev/null 2>&1; do sleep 20; done
for m in B0 B1 B2 B1R; do
  .venv/Scripts/python.exe -X utf8 -m cipher.run --method $m --split calibration --run-id dev1-$m-calibration
done
