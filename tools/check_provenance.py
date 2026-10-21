"""Recompute stored hashes: every snapshot file, the case manifest, and every issued packet body."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cipher.acquire import DISCOVERY_CSV, DISCOVERY_SHA256, verify  # noqa: E402

errors = []
if hashlib.sha256(DISCOVERY_CSV.read_bytes()).hexdigest() != DISCOVERY_SHA256:
    errors.append("discovery CSV hash mismatch")
for f in sorted((ROOT / "data" / "snapshots").glob("*.json")):
    errors += verify(json.loads(f.read_text(encoding="utf-8")))
freeze = (ROOT / "docs" / "freeze.md").read_text(encoding="utf-8")
man = hashlib.sha256((ROOT / "data" / "cases" / "manifest.json").read_bytes()).hexdigest()
if man not in freeze:
    errors.append(f"manifest hash {man} not recorded in docs/freeze.md")
cases = {c["case_id"]: c for c in json.loads((ROOT / "data" / "cases" / "manifest.json").read_text(encoding="utf-8"))}
for k in sorted((ROOT / "annotations" / "keys").glob("CIPHER-*_A*.json")):
    key = json.loads(k.read_text(encoding="utf-8"))
    for oid, v in key["items"].items():
        if cases[v["case_id"]]["case_sha256"] != v["case_sha256"]:
            errors.append(f"{k.name}: {v['case_id']} changed after the packet was issued")
print("\n".join(errors) or "provenance ok")
sys.exit(1 if errors else 0)
