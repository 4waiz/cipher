"""Unlock sealed held-out runs once the human reference labels are final.

Checks that every evaluation original and context variant has a final reference label (agreed or adjudicated, or is
explicitly excluded), verifies each sealed run's predictions hash against its run manifest, copies the runs to
runs/heldout/ (committed), and records the unlock in runs/heldout/UNLOCK.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

from .acquire import ROOT


def main() -> None:
    ref = json.loads((ROOT / "annotations" / "reference_labels.json").read_text(encoding="utf-8"))
    pending = [r["case_id"] for r in ref if r["stratum"] != "order_control" and r["status"] == "pending"]
    if pending:
        sys.exit(f"{len(pending)} reference labels still pending: {pending[:5]}...")
    runs = json.loads((ROOT / "configs" / "heldout_runs.json").read_text(encoding="utf-8"))
    dest = ROOT / "runs" / "heldout"
    dest.mkdir(parents=True, exist_ok=True)
    record = {"unlocked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "reference_labels_sha256": hashlib.sha256(
                  (ROOT / "annotations" / "reference_labels.json").read_bytes()).hexdigest(), "runs": {}}
    for method, rid in runs.items():
        src = ROOT / "runs" / "sealed" / rid
        man = json.loads((src / "run_manifest.json").read_text(encoding="utf-8"))
        h = hashlib.sha256((src / "predictions.jsonl").read_bytes()).hexdigest()
        if h != man["predictions_sha256"]:
            sys.exit(f"{rid}: predictions changed after the run finished")
        shutil.copytree(src, dest / rid, dirs_exist_ok=True)
        record["runs"][method] = {"run_id": rid, "predictions_sha256": h,
                                  "finished_at": man["sessions"][-1]["finished_at"]}
    (dest / "UNLOCK.json").write_text(json.dumps(record, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
