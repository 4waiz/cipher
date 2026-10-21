"""Execute one method over one split and record a complete run manifest.

Evaluation-split runs are written to runs/sealed/ (git-ignored) and the console shows only completion counts, never
labels, until the reference labels are final (see docs/protocol.md). Calibration and practice runs go to runs/dev/.
Runs resume: cases already present in predictions.jsonl are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata

from .acquire import ROOT
from .llm import ModelConfig, check_model, installed_digest
from .methods import PROMPTS, b0, b1, b1r, b2
from .practice import practice_items

METHODS = {"B0": b0, "B1": b1, "B1R": b1r, "B2": b2}


def git_state() -> dict:
    def g(*a: str) -> str:
        return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return {"commit": g("rev-parse", "HEAD"),
            "dirty": bool(g("status", "--porcelain", "--", "src", "configs", "data", "docs/analysis_plan.md"))}


CODE_FILES = ["src/cipher/profile.py", "src/cipher/methods.py", "src/cipher/llm.py", "src/cipher/run.py",
              "src/cipher/practice.py", "data/cases/manifest.json"]


def model_details(model: str) -> dict:
    """Quantization and family as reported by the Ollama server (recorded, not trusted for identity: the digest is)."""
    import requests
    from .llm import OLLAMA
    d = requests.post(f"{OLLAMA}/api/show", json={"model": model}, timeout=30).json().get("details", {})
    return {k: d.get(k) for k in ("family", "parameter_size", "quantization_level", "format")}


def sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cases(split: str) -> list[dict]:
    if split == "practice":
        return practice_items()
    cases = json.loads((ROOT / "data" / "cases" / "manifest.json").read_text(encoding="utf-8"))
    return [c for c in cases if c["split"] == split]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--method", choices=METHODS, required=True)
    ap.add_argument("--split", choices=["practice", "calibration", "evaluation"], required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--model", default=ModelConfig.model)
    ap.add_argument("--no-think", action="store_true")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    sealed = args.split == "evaluation"
    out = ROOT / "runs" / ("sealed" if sealed else "dev") / args.run_id
    out.mkdir(parents=True, exist_ok=True)
    cfg = ModelConfig(model=args.model, think=not args.no_think)
    if args.method != "B0":
        if args.model != ModelConfig.model:
            cfg.digest = installed_digest(args.model) or "missing"
        check_model(cfg)
    cases = load_cases(args.split)[: args.limit]
    pred_file = out / "predictions.jsonl"
    done = set()
    if pred_file.exists():
        done = {json.loads(ln)["case_id"] for ln in pred_file.read_text(encoding="utf-8").splitlines() if ln.strip()}
    manifest_path = out / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "run_id": args.run_id, "method": args.method, "split": args.split, "sealed": sealed,
        "started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": None if args.method == "B0" else cfg.__dict__,
        "model_details": None if args.method == "B0" else model_details(cfg.model),
        "prompts_sha256": {p.name: sha(p) for p in sorted(PROMPTS.glob("*.txt"))},
        "code_sha256": {f: sha(ROOT / f) for f in CODE_FILES},
        "case_manifest_sha256": sha(ROOT / "data" / "cases" / "manifest.json"),
        "code": git_state(), "python": sys.version.split()[0], "platform": platform.platform(),
        "packages": {p: metadata.version(p) for p in ("requests", "numpy", "matplotlib")},
        "sessions": []}
    session = {"started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "code": git_state(),
               "digest_before": None if args.method == "B0" else installed_digest(cfg.model)}
    n_ok = n_err = 0
    with pred_file.open("a", encoding="utf-8", newline="\n") as fh:
        for c in cases:
            if c["case_id"] in done:
                continue
            res = METHODS[args.method](c) if args.method == "B0" else METHODS[args.method](c, cfg)
            rec = {"case_id": c["case_id"], "case_sha256": c.get("case_sha256"), "method": args.method,
                   "run_id": args.run_id, **res}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            if res.get("error"):
                n_err += 1
            else:
                n_ok += 1
            if sealed:  # progress only: per-case calls or tokens could reveal B2's short-circuit outcomes
                print(f"{n_ok + n_err + len(done)}/{len(cases)} done", flush=True)
            else:
                status = "error" if res.get("error") else "ok"
                print(f"{c['case_id']}: {status} -> {res.get('label', res.get('conflict_flag'))} "
                      f"calls={res.get('calls', 0)} tok={res.get('input_tokens', 0)}/{res.get('output_tokens', 0)} "
                      f"{res.get('latency_s', 0)}s", flush=True)
    session.update(finished_at=datetime.now(timezone.utc).isoformat(timespec="seconds"), ok=n_ok, errors=n_err,
                   digest_after=None if args.method == "B0" else installed_digest(cfg.model))
    if session["digest_before"] != session["digest_after"]:
        session["warning"] = "model digest changed during the session"
    manifest["sessions"].append(session)
    manifest["predictions_sha256"] = sha(pred_file)
    manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8", newline="\n")
    print(f"done: ok={n_ok} errors={n_err} -> {out}")


if __name__ == "__main__":
    main()
