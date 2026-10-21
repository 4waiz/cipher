"""Engineering fixture for analysis/results.py: synthetic labels and predictions in a temporary directory.

The synthetic values exist only inside pytest's tmp_path; nothing is written to research-result directories."""

import importlib.util
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["Unresolved conflict", "Valid override", "Disjoint applicability", "Compatible", "Insufficient evidence"]


def load_results_module(tmp: Path):
    spec = importlib.util.spec_from_file_location("results_under_test", ROOT / "analysis" / "results.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT = tmp
    mod.EXPORTS, mod.TABLES = tmp / "analysis/exports", tmp / "analysis/tables"
    mod.GEN, mod.FIGS = tmp / "paper/generated", tmp / "paper/build/figures"
    return mod


def test_results_available_path(tmp_path):
    (tmp_path / "data/cases").mkdir(parents=True)
    shutil.copy(ROOT / "data/cases/manifest.json", tmp_path / "data/cases/manifest.json")
    cases = json.loads((tmp_path / "data/cases/manifest.json").read_text(encoding="utf-8"))
    ev = [c for c in cases if c["split"] == "evaluation"]
    rng = random.Random(0)
    ref = {}
    for c in ev:
        if c["stratum"] != "order_control":
            ref[c["case_id"]] = {"case_id": c["case_id"], "stratum": c["stratum"], "a1": None, "a2": None,
                                 "label": rng.choice(LABELS), "status": "agreed", "adjudication_reason": None}
    for c in ev:
        if c["stratum"] == "order_control":
            ref[c["case_id"]] = {"case_id": c["case_id"], "stratum": "order_control",
                                 "parent_case_id": c["parent_case_id"], "label": ref[c["parent_case_id"]]["label"],
                                 "status": "inherited"}
    (tmp_path / "annotations").mkdir()
    (tmp_path / "annotations/reference_labels.json").write_text(json.dumps(list(ref.values())))
    (tmp_path / "configs").mkdir()
    runs = {m: f"fx-{m}" for m in ("B0", "B1", "B2", "B1R")}
    (tmp_path / "configs/heldout_runs.json").write_text(json.dumps(runs))
    (tmp_path / "runs/heldout").mkdir(parents=True)
    (tmp_path / "runs/heldout/UNLOCK.json").write_text("{}")
    for m, rid in runs.items():
        d = tmp_path / "runs/heldout" / rid
        d.mkdir()
        lines = []
        for c in ev:
            if m == "B0":
                rec = {"case_id": c["case_id"], "conflict_flag": rng.random() < 0.2}
            else:
                lab = rng.choice(LABELS + [None])
                rec = {"case_id": c["case_id"], "label": lab, "abstained": lab is None, "error": None,
                       "explanation": "x", "evidence": [f"{c['packet']['rule_1']['path']}:"
                                                        f"{c['packet']['rule_1']['start_line']}", "nope:1"],
                       "calls": 1, "input_tokens": 10, "output_tokens": 5, "latency_s": 1.0, "retries": 0}
            lines.append(json.dumps(rec))
        (d / "predictions.jsonl").write_text("\n".join(lines))
    mod = load_results_module(tmp_path)
    mod.main()
    metrics = json.loads((tmp_path / "analysis/exports/metrics.json").read_text())
    assert metrics["strata_n"] == {"original": 27, "context_variant": 27, "order_control": 27}
    assert metrics["methods"]["B1"]["original"]["anchors"]["cited"] == 54
    assert metrics["methods"]["B1"]["original"]["anchors"]["valid"] == 27  # 'nope:1' never validates
    assert (tmp_path / "paper/generated/tab_methods.tex").read_text().count("\\\\") >= 6
    assert (tmp_path / "paper/build/figures/confusion.svg").exists()
    res = json.loads((tmp_path / "analysis/exports/results.json").read_text())
    assert res["available"] and {t["id"] for t in res["tables"]} >= {"support", "methods", "binary", "paired"}
    replay = json.loads((tmp_path / "analysis/exports/replay.json").read_text())
    assert len(replay["cases"]) == 81
