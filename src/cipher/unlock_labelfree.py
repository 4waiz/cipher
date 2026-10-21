"""Unlock the sealed primary held-out runs for the label-free analysis (docs/analysis_plan.md, addendum A2).

Used because the human annotation was not carried out. Verifies each run's predictions hash against its manifest,
copies the runs to runs/heldout/, and records the mode, the plan and analysis-code hashes in runs/heldout/UNLOCK.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

from .acquire import ROOT

CODE = ["analysis/labelfree.py", "src/cipher/metrics.py", "src/cipher/profile.py", "src/cipher/unlock_labelfree.py",
        "docs/analysis_plan.md"]


def sha(p) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    runs = json.loads((ROOT / "configs" / "heldout_runs.json").read_text(encoding="utf-8"))
    dest = ROOT / "runs" / "heldout"
    dest.mkdir(parents=True, exist_ok=True)
    record = {"unlocked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "mode": "label-free: no human reference labels exist (analysis plan addendum A2)",
              "analysis_code_sha256": {f: sha(ROOT / f) for f in CODE}, "runs": {}}
    for method, rid in runs.items():
        src = ROOT / "runs" / "sealed" / rid
        man = json.loads((src / "run_manifest.json").read_text(encoding="utf-8"))
        h = sha(src / "predictions.jsonl")
        if h != man["predictions_sha256"]:
            sys.exit(f"{rid}: predictions changed after the run finished")
        n = len([x for x in (src / "predictions.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()])
        shutil.copytree(src, dest / rid, dirs_exist_ok=True)
        record["runs"][method] = {"run_id": rid, "predictions_sha256": h, "records": n}
    (dest / "UNLOCK.json").write_text(json.dumps(record, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
