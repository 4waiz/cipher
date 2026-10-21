"""Unlock sealed held-out runs once the human reference labels are final.

Checks that every evaluation original and context variant has a final reference label or a recorded exclusion,
verifies each sealed run's predictions hash against its run manifest, copies the primary and secondary runs to
runs/heldout/ (committed), and records the unlock, the reference-label hash and the analysis-code hashes in
runs/heldout/UNLOCK.json.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone

from .acquire import ROOT

ANALYSIS_CODE = ["analysis/results.py", "src/cipher/metrics.py", "src/cipher/reference.py", "src/cipher/unlock.py",
                 "docs/analysis_plan.md"]


def sha(p) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    ref = json.loads((ROOT / "annotations" / "reference_labels.json").read_text(encoding="utf-8"))
    pending = [r["case_id"] for r in ref if r["stratum"] == "original" and r["status"] == "pending"]
    pending += [r["case_id"] for r in ref if r["stratum"] == "context_variant"
                and r["status"] in ("pending", "pending_transformation_review")]
    if pending:
        sys.exit(f"{len(pending)} reference labels still pending: {pending[:5]}...")
    runs = {"primary": json.loads((ROOT / "configs" / "heldout_runs.json").read_text(encoding="utf-8"))}
    sec = ROOT / "configs" / "secondary_runs.json"
    if sec.exists():
        runs["secondary"] = json.loads(sec.read_text(encoding="utf-8"))
    dest = ROOT / "runs" / "heldout"
    dest.mkdir(parents=True, exist_ok=True)
    record = {"unlocked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "reference_labels_sha256": sha(ROOT / "annotations" / "reference_labels.json"),
              "analysis_code_sha256": {f: sha(ROOT / f) for f in ANALYSIS_CODE}, "runs": {}}
    for group, rs in runs.items():
        for method, rid in rs.items():
            src = ROOT / "runs" / "sealed" / rid
            man = json.loads((src / "run_manifest.json").read_text(encoding="utf-8"))
            h = sha(src / "predictions.jsonl")
            if h != man["predictions_sha256"]:
                sys.exit(f"{rid}: predictions changed after the run finished")
            shutil.copytree(src, dest / rid, dirs_exist_ok=True)
            record["runs"][f"{group}:{method}"] = {"run_id": rid, "predictions_sha256": h,
                                                   "finished_at": man["sessions"][-1]["finished_at"]}
    (dest / "UNLOCK.json").write_text(json.dumps(record, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()
