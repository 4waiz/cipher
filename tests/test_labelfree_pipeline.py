"""Engineering fixture for analysis/labelfree.py: synthetic predictions inside pytest's tmp_path only."""

import importlib.util
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = ["Unresolved conflict", "Valid override", "Disjoint applicability", "Compatible", "Insufficient evidence"]


def test_labelfree_path(tmp_path):
    (tmp_path / "data/cases").mkdir(parents=True)
    shutil.copy(ROOT / "data/cases/manifest.json", tmp_path / "data/cases/manifest.json")
    cases = [c for c in json.loads((tmp_path / "data/cases/manifest.json").read_text(encoding="utf-8"))
             if c["split"] == "evaluation"]
    runs = {m: f"fx-{m}" for m in ("B0", "B1", "B2", "B1R")}
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/heldout_runs.json").write_text(json.dumps(runs))
    (tmp_path / "runs/heldout").mkdir(parents=True)
    (tmp_path / "runs/heldout/UNLOCK.json").write_text("{}")
    rng = random.Random(1)
    for m, rid in runs.items():
        d = tmp_path / "runs/heldout" / rid
        d.mkdir()
        lines = []
        for c in cases:
            if m == "B0":
                rec = {"case_id": c["case_id"], "conflict_flag": rng.random() < 0.2}
            else:
                lab = "Disjoint applicability" if m == "B2" else rng.choice(LABELS)
                rec = {"case_id": c["case_id"], "label": lab, "abstained": False, "error": None, "first_label": lab,
                       "explanation": "x", "evidence": [], "calls": 1, "input_tokens": 10, "output_tokens": 5,
                       "latency_s": 1.0, "retries": 0, "attempts": [{"status": "ok"}]}
            lines.append(json.dumps(rec))
        (d / "predictions.jsonl").write_text("\n".join(lines))
    spec = importlib.util.spec_from_file_location("labelfree_under_test", ROOT / "analysis" / "labelfree.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT, mod.EXPORTS, mod.TABLES = tmp_path, tmp_path / "analysis/exports", tmp_path / "analysis/tables"
    mod.GEN, mod.FIGS = tmp_path / "paper/generated", tmp_path / "paper/build/figures"
    mod.main()
    m = json.loads((tmp_path / "analysis/exports/metrics.json").read_text())
    assert m["pd"] == {"all": 26, "main": 21, "by_stratum": {"original": 5, "context_variant": 16, "order_control": 5}}
    assert m["methods"]["B2"]["pd_correct_main"] == {"k": 21, "n": 21}  # synthetic B2 always says Disjoint
    assert m["methods"]["B2"]["order_stable"]["k"] == 27
    assert (tmp_path / "paper/generated/tab_results.tex").exists()
    assert (tmp_path / "paper/build/figures/labels.svg").exists()
    assert len(json.loads((tmp_path / "analysis/exports/replay.json").read_text())["cases"]) == 81
