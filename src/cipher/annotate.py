"""Build blinded, independently randomised annotation packets (standalone HTML files).

Each annotator gets their own item order (recorded seed) and opaque item IDs. Packets never contain model predictions,
proposed labels, strata, transformation descriptions, family IDs, or the other annotator's answers. The ID key that maps
opaque item IDs back to case IDs is written separately to annotations/keys/.
"""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from .acquire import ROOT
from .practice import practice_items
from .profile import PROFILE_TEXT

TOOL_VERSION = "annotate-1.0"
HANDBOOK = ROOT / "docs" / "annotation_handbook.md"
TEMPLATE = Path(__file__).parent / "templates" / "annotate.html"
OUT = ROOT / "annotations" / "packets"
KEYS = ROOT / "annotations" / "keys"
ANNOTATORS = {"A1": "Awaiz Ahmed", "A2": "Mohammad Umar"}
SEED = 20261021
VISIBLE = ("task", "target_path", "repo", "commit", "packet")


def opaque_id(seed: int, annotator: str, case_id: str) -> str:
    return "c" + hashlib.sha256(f"{seed}|{annotator}|{case_id}".encode()).hexdigest()[:6]


def handbook_version() -> str:
    text = HANDBOOK.read_text(encoding="utf-8")
    return text.splitlines()[0].split("(")[-1].rstrip(")") + " sha256:" + hashlib.sha256(text.encode()).hexdigest()[:12]


def build(packet_name: str, title: str, cases: list[dict], practice: list[dict], annotator: str) -> Path:
    seed = int(hashlib.sha256(f"{SEED}|{packet_name}|{annotator}".encode()).hexdigest()[:8], 16)
    order = sorted(cases, key=lambda c: c["case_id"])
    random.Random(seed).shuffle(order)
    items, key = [], {}
    for p in practice:
        items.append({"item_id": p["case_id"], "practice": True, **{k: p[k] for k in VISIBLE},
                      "practice_answer": p["practice_answer"], "practice_explanation": p["practice_explanation"]})
    for c in order:
        oid = opaque_id(seed, annotator, c["case_id"])
        key[oid] = {"case_id": c["case_id"], "case_sha256": c["case_sha256"]}
        items.append({"item_id": oid, "practice": False, **{k: c[k] for k in VISIBLE}})
    body = json.dumps(items, sort_keys=True, ensure_ascii=False)
    packet = {"packet_id": f"CIPHER-{packet_name}", "title": title, "annotator_id": annotator,
              "annotator_name": ANNOTATORS[annotator], "seed": seed, "tool_version": TOOL_VERSION,
              "handbook_version": handbook_version(), "profile_text": PROFILE_TEXT,
              "packet_sha256": hashlib.sha256(body.encode()).hexdigest(), "items": items}
    html = TEMPLATE.read_text(encoding="utf-8")
    data = json.dumps(packet, ensure_ascii=False).replace("</", "<\\/")
    hb = HANDBOOK.read_text(encoding="utf-8").replace("</", "<\\/")
    html = html.replace("/*__PACKET__*/", data).replace("/*__HANDBOOK__*/", hb)
    OUT.mkdir(parents=True, exist_ok=True)
    KEYS.mkdir(parents=True, exist_ok=True)
    path = OUT / f"CIPHER_{packet_name}_{annotator}.html"
    path.write_text(html, encoding="utf-8", newline="\n")
    (KEYS / f"CIPHER-{packet_name}_{annotator}.json").write_text(
        json.dumps({"packet_id": packet["packet_id"], "annotator_id": annotator, "seed": seed,
                    "packet_sha256": packet["packet_sha256"], "items": key}, indent=1), encoding="utf-8", newline="\n")
    return path


def main() -> None:
    cases = json.loads((ROOT / "data" / "cases" / "manifest.json").read_text(encoding="utf-8"))
    calib = [c for c in cases if c["split"] == "calibration"]
    evalc = [c for c in cases if c["split"] == "evaluation" and c["stratum"] in ("original", "context_variant")]
    practice = practice_items()
    for a in ANNOTATORS:
        p1 = build("calibration", "Calibration packet", calib, practice, a)
        p2 = build("evaluation", "Evaluation packet", evalc, [], a)
        print(a, p1.name, len(practice) + len(calib), p2.name, len(evalc))


if __name__ == "__main__":
    main()
