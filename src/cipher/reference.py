"""Reference labels from genuine human submissions.

  python -m cipher.reference status        # which submissions exist and whether they are complete
  python -m cipher.reference adjudication  # after both independent evaluation files exist: agreement + Huda's packet
  python -m cipher.reference review        # transformation-validity checklist (variants and order controls)
  python -m cipher.reference finalize      # merge agreed, adjudicated and inherited labels into reference_labels.json

Nothing here invents or pre-fills a judgment. Missing submissions leave labels pending.
"""

from __future__ import annotations

import hashlib
import html
import json
import random
import sys
from collections import Counter

from . import annotate
from .acquire import ROOT
from .metrics import LABELS, cohen_kappa

SUB = ROOT / "annotations" / "submissions"
ADJ = ROOT / "annotations" / "adjudication"
KEYS = ROOT / "annotations" / "keys"
OUT = ROOT / "annotations" / "reference_labels.json"
STATS = ROOT / "annotations" / "agreement.json"


def manifest() -> dict[str, dict]:
    cases = json.loads((ROOT / "data" / "cases" / "manifest.json").read_text(encoding="utf-8"))
    return {c["case_id"]: c for c in cases}


def load_submission(packet: str, annotator: str) -> dict[str, dict] | None:
    """Responses keyed by case_id, after checking the packet hash against the recorded key."""
    f = SUB / f"{packet}_{annotator}.json"
    if not f.exists():
        return None
    sub = json.loads(f.read_text(encoding="utf-8"))
    key = json.loads((KEYS / f"CIPHER-{packet}_{annotator}.json").read_text(encoding="utf-8"))
    if sub.get("packet_sha256") != key["packet_sha256"] or sub.get("annotator_id") != annotator:
        sys.exit(f"{f.name}: packet hash or annotator does not match the issued packet")
    out = {}
    for r in sub["responses"]:
        if r["item_id"] in key["items"]:
            out[key["items"][r["item_id"]]["case_id"]] = r
    return out


def complete(r: dict | None) -> bool:
    return bool(r and r.get("label") in LABELS and (r.get("reason") or "").strip())


def status() -> None:
    for packet in ("calibration", "evaluation"):
        for a in annotate.ANNOTATORS:
            s = load_submission(packet, a)
            if s is None:
                print(f"{packet}_{a}: not received")
            else:
                n = sum(complete(r) for r in s.values())
                mins = sum((r.get("active_ms") or 0) for r in s.values()) / 60000
                print(f"{packet}_{a}: {n}/{len(s)} complete, active time {mins:.0f} min")


def agreement(packet: str) -> dict:
    m = manifest()
    a1, a2 = load_submission(packet, "A1"), load_submission(packet, "A2")
    if a1 is None or a2 is None:
        sys.exit("both independent submissions are required first")
    res = {}
    for stratum in ("original", "context_variant"):
        ids = sorted(c for c in a1 if c in a2 and m[c]["stratum"] == stratum and complete(a1[c]) and complete(a2[c]))
        la, lb = [a1[c]["label"] for c in ids], [a2[c]["label"] for c in ids]
        table = {x: {y: sum(1 for p, q in zip(la, lb) if p == x and q == y) for y in LABELS} for x in LABELS}
        res[stratum] = {**cohen_kappa(la, lb), "a1_counts": dict(Counter(la)), "a2_counts": dict(Counter(lb)),
                        "table_a1_rows_a2_cols": table}
    return res


def adjudication() -> None:
    m = manifest()
    a1, a2 = load_submission("evaluation", "A1"), load_submission("evaluation", "A2")
    if a1 is None or a2 is None:
        sys.exit("both independent evaluation submissions are required first")
    incomplete = [c for c in a1 if not (complete(a1.get(c)) and complete(a2.get(c)))]
    if incomplete:
        sys.exit(f"{len(incomplete)} items are incomplete in at least one submission; adjudication waits")
    STATS.write_text(json.dumps({"evaluation": agreement("evaluation")}, indent=1), encoding="utf-8", newline="\n")
    dis = sorted(c for c in a1 if a1[c]["label"] != a2[c]["label"])
    rng = random.Random(20261021)
    rng.shuffle(dis)
    items = []
    for cid in dis:
        js = [("A1", a1[cid]), ("A2", a2[cid])]
        rng.shuffle(js)  # the adjudicator sees "Annotator X/Y", not names
        judg = [{"who": f"Annotator {'XY'[i]}", **{k: j.get(k) for k in ("label", "reason", "evidence", "applies_1",
                 "applies_2", "incompatible", "winner", "confidence", "missing_context")}} for i, (_, j) in enumerate(js)]
        oid = "d" + hashlib.sha256(f"adj|{cid}".encode()).hexdigest()[:6]
        items.append({"item_id": oid, "practice": False, "judgments": judg,
                      **{k: m[cid][k] for k in annotate.VISIBLE}, "_case_id": cid,
                      "_order": [w for w, _ in js]})
    key = {it["item_id"]: {"case_id": it.pop("_case_id"), "judgment_order": it.pop("_order")} for it in items}
    body = json.dumps(items, sort_keys=True, ensure_ascii=False)
    packet = {"packet_id": "CIPHER-adjudication", "title": "Adjudication packet", "annotator_id": "ADJ",
              "annotator_name": "Huda Mueen", "seed": 20261021, "tool_version": annotate.TOOL_VERSION,
              "handbook_version": annotate.handbook_version(), "profile_text": annotate.PROFILE_TEXT,
              "packet_sha256": hashlib.sha256(body.encode()).hexdigest(), "items": items}
    tpl = annotate.TEMPLATE.read_text(encoding="utf-8")
    page = tpl.replace("/*__PACKET__*/", json.dumps(packet, ensure_ascii=False).replace("</", "<\\/")).replace(
        "/*__HANDBOOK__*/", annotate.HANDBOOK.read_text(encoding="utf-8").replace("</", "<\\/"))
    ADJ.mkdir(parents=True, exist_ok=True)
    (ADJ / "CIPHER_adjudication_Huda.html").write_text(page, encoding="utf-8", newline="\n")
    (KEYS / "CIPHER-adjudication_ADJ.json").write_text(json.dumps(
        {"packet_id": packet["packet_id"], "packet_sha256": packet["packet_sha256"], "items": key}, indent=1),
        encoding="utf-8", newline="\n")
    print(f"{len(dis)} disagreements of {len(a1)} -> annotations/adjudication/CIPHER_adjudication_Huda.html")


def review() -> None:
    """Static checklist for the human transformation-validity check (no labels shown)."""
    m = manifest()
    rows = []
    for c in sorted(m.values(), key=lambda c: c["case_id"]):
        if c["split"] != "evaluation" or c["stratum"] == "original":
            continue
        p, ch = m[c["parent_case_id"]]["packet"], c["packet"]
        def r(pk, n):
            x = pk[f"rule_{n}"]
            return f"{x['path']}:{x['start_line']}-{x['end_line']} [heading: {x['heading'] or 'none'}] | {x['text']}"
        rows.append(f"""<tr><td class=mono>{c['case_id']}</td><td>{html.escape(c['transformation'])}</td>
<td class=mono>{html.escape(m[c['parent_case_id']]['target_path'])}<br>1: {html.escape(r(p, 1))}<br>2: {html.escape(r(p, 2))}</td>
<td class=mono>{html.escape(c['target_path'])}<br>1: {html.escape(r(ch, 1))}<br>2: {html.escape(r(ch, 2))}</td>
<td><label><input type=checkbox data-id="{c['case_id']}"> valid</label><br><input data-note="{c['case_id']}" placeholder=note></td></tr>""")
    page = f"""<!doctype html><meta charset=utf-8><title>CIPHER transformation review</title>
<style>body{{font:14px system-ui;margin:16px}}td,th{{border:1px solid #ccc;padding:6px;vertical-align:top}}table{{border-collapse:collapse}}
.mono{{font-family:Consolas,monospace;font-size:12px}}</style>
<h1>Transformation validity review</h1><p>Tick "valid" when the child differs from its parent only in the declared
property (target path, placement of one instruction, or order of the two instructions) and every instruction's wording
is unchanged. A relocated instruction keeps only its nearest heading; leave "valid" unticked and add a note if losing an
outer heading changes what the instruction means or where it applies. Do this after adjudication. Then click Export
and save the file as annotations/submissions/transformation_review.json.</p><button onclick="exp()">Export JSON</button>
<table><tr><th>Case</th><th>Declared change</th><th>Parent</th><th>Child</th><th>Check</th></tr>{''.join(rows)}</table>
<script>function exp(){{const r={{reviewer:"Huda Mueen",exported_at:new Date().toISOString(),items:{{}}}};
document.querySelectorAll('input[data-id]').forEach(e=>{{r.items[e.dataset.id]={{valid:e.checked,note:document.querySelector(`input[data-note="${{e.dataset.id}}"]`).value}}}});
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(r,null,1)]));a.download='transformation_review.json';a.click();}}</script>"""
    ADJ.mkdir(parents=True, exist_ok=True)
    (ADJ / "CIPHER_transformation_review.html").write_text(page, encoding="utf-8", newline="\n")
    print(f"{len(rows)} transformations -> annotations/adjudication/CIPHER_transformation_review.html")


def finalize() -> None:
    m = manifest()
    a1, a2 = load_submission("evaluation", "A1") or {}, load_submission("evaluation", "A2") or {}
    adj = {}
    f = SUB / "adjudication_ADJ.json"
    if f.exists():
        sub = json.loads(f.read_text(encoding="utf-8"))
        key = json.loads((KEYS / "CIPHER-adjudication_ADJ.json").read_text(encoding="utf-8"))
        if sub.get("packet_sha256") != key["packet_sha256"]:
            sys.exit("adjudication file does not match the issued packet")
        adj = {key["items"][r["item_id"]]["case_id"]: r for r in sub["responses"] if complete(r)}
    rv = {}
    f = SUB / "transformation_review.json"
    if f.exists():
        rv = json.loads(f.read_text(encoding="utf-8"))["items"]
    out = {}
    for cid, c in sorted(m.items()):
        if c["split"] != "evaluation" or c["stratum"] == "order_control":
            continue
        r1, r2 = a1.get(cid), a2.get(cid)
        rec = {"case_id": cid, "stratum": c["stratum"], "a1": r1.get("label") if r1 else None,
               "a2": r2.get("label") if r2 else None, "label": None, "status": "pending", "adjudication_reason": None}
        if complete(r1) and complete(r2) and r1["label"] == r2["label"]:
            rec.update(label=r1["label"], status="agreed")
        elif cid in adj:
            rec.update(label=adj[cid]["label"], status="adjudicated", adjudication_reason=adj[cid]["reason"])
        if c["stratum"] == "context_variant" and rec["label"] and not rv.get(cid, {}).get("valid"):
            # declared in docs/analysis_plan.md (addendum A1): a variant is scored only after a human confirmed it
            rec.update(status="pending_transformation_review" if not rv else "excluded_transformation_not_verified",
                       label=None)
        out[cid] = rec
    for cid, c in sorted(m.items()):
        if c["split"] == "evaluation" and c["stratum"] == "order_control":
            parent = out.get(c["parent_case_id"], {})
            ok = rv.get(cid, {}).get("valid")
            out[cid] = {"case_id": cid, "stratum": "order_control", "parent_case_id": c["parent_case_id"],
                        "label": parent.get("label") if ok else None,
                        "status": ("inherited" if parent.get("label") else "pending") if ok else
                        "pending_transformation_review"}
    OUT.write_text(json.dumps(list(out.values()), indent=1), encoding="utf-8", newline="\n")
    print(Counter(r["status"] for r in out.values()))


if __name__ == "__main__":
    {"status": status, "adjudication": adjudication, "review": review, "finalize": finalize}[sys.argv[1]]()
