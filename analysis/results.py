"""Compute every reported result from saved evidence, following docs/analysis_plan.md.

Inputs : annotations/reference_labels.json (final human labels), annotations/agreement.json,
         runs/heldout/<run_id>/predictions.jsonl for the run IDs in configs/heldout_runs.json, data/cases/manifest.json
Outputs: analysis/exports/{metrics,results,replay,status}.json, analysis/tables/*.csv,
         paper/generated/results.tex (numeric macros and tables), paper/build/figures/*.{pdf,svg}

If reference labels are not final or held-out runs are not unlocked, only execution facts are exported and the paper
macros state that results are pending. No accuracy number is computed without final human reference labels.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cipher import metrics as M  # noqa: E402
from cipher.metrics import CONFLICT, LABELS  # noqa: E402

EXPORTS = ROOT / "analysis" / "exports"
TABLES = ROOT / "analysis" / "tables"
GEN = ROOT / "paper" / "generated"
FIGS = ROOT / "paper" / "build" / "figures"
VERSION = "0.9.0"
VERSION_DATE = "2026-10-21"  # date of the results revision shown on the site
SHORT = {"Unresolved conflict": "Conflict", "Valid override": "Override", "Disjoint applicability": "Disjoint",
         "Compatible": "Compatible", "Insufficient evidence": "Insufficient"}
METHODS = ["B1", "B2", "B1R"]


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def fmt(x, pct=False, nd=2) -> str:
    if x is None:
        return "--"
    return f"{100 * x:.0f}\\%" if pct else f"{x:.{nd}f}"


def git_commit() -> str:
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def load_json(p: Path, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def load_predictions(run_dirs: dict[str, str]) -> dict[str, dict[str, dict]]:
    out = {}
    for m, d in run_dirs.items():
        f = ROOT / d / "predictions.jsonl"
        if f.exists():
            out[m] = {json.loads(ln)["case_id"]: json.loads(ln) for ln in f.read_text(encoding="utf-8").splitlines()
                      if ln.strip()}
    return out


def execution_table(preds: dict, ids: list[str]) -> list[list]:
    rows = []
    for m in ["B0"] + METHODS:
        p = preds.get(m)
        if not p:
            continue
        rs = [p[c] for c in ids if c in p]
        rows.append([m, len(rs), sum(1 for r in rs if r.get("error")), sum(1 for r in rs if r.get("abstained")),
                     sum(r.get("retries", 0) for r in rs), sum(r.get("calls", 0) for r in rs),
                     round(sum(r.get("input_tokens", 0) for r in rs) / max(len(rs), 1)),
                     round(sum(r.get("output_tokens", 0) for r in rs) / max(len(rs), 1)),
                     round(sum(r.get("latency_s", 0) for r in rs) / max(len(rs), 1), 1)])
    return rows


def anchor_validity(case: dict, evidence: list[str]) -> tuple[int, int]:
    pk = case["packet"]
    rules = [pk["rule_1"], pk["rule_2"]]  # same-file pairs share a path, so check each rule's shown section
    scope = {(s["path"], s["line"]) for s in pk["scope_statements"]}
    ok = 0
    for e in evidence:
        path, _, rng = e.strip().rpartition(":")
        try:
            lo = int(rng.split("-")[0])
        except ValueError:
            continue
        if any(r["path"] == path and r["section_first_line"] <= lo <= r["section_last_line"] for r in rules) \
                or (path, lo) in scope:
            ok += 1
    return ok, len(evidence)


def pending(reason: str, preds: dict, cases: dict) -> None:
    ids = [c for c, x in cases.items() if x["split"] == "evaluation"]
    ex = execution_table(preds, ids)
    status = {"version": VERSION, "date": VERSION_DATE,
              "status_label": "Pilot study in progress: human reference labels pending", "results_available": False}
    cols = ["Method", "Cases run", "Failures", "Abstentions", "Retries", "Calls", "Mean input tokens",
            "Mean output tokens", "Mean latency (s)"]
    results = {"available": False, "reason": reason,
               "tables": ([{"id": "execution", "title": "Execution record (no accuracy)",
                            "caption": "Completion facts for sealed held-out runs. No label or accuracy is shown "
                                       "before the human reference labels are final.",
                            "columns": cols, "rows": ex, "notes": ""}] if ex else []),
               "figures": [], "limitations": []}
    EXPORTS.mkdir(parents=True, exist_ok=True)
    w(EXPORTS / "status.json", json.dumps(status, indent=1))
    w(EXPORTS / "results.json", json.dumps(results, indent=1))
    w(EXPORTS / "replay.json", json.dumps({"available": False, "reason": reason, "cases": []}, indent=1))
    w(GEN / "results.tex", "% Generated by analysis/results.py. Results pending.\n"
      "\\newcommand{\\ResultsHeadline}{results once the human reference labels are final.}\n"
      "\\newcommand{\\ResultsSection}{\\textbf{Pending.} " + reason + "}\n"
      "\\newcommand{\\AbstractText}{\\textbf{Draft: results pending human reference labels.}}\n"
      "\\newcommand{\\ConclusionText}{Pending.}\n"
      "\\newcommand{\\AIDisclosure}{Pending.}\n")
    print("pending:", reason)


def confusion_figure(gold: dict[str, list], preds_lab: dict[str, list], present: list[str], n: int) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 7, "svg.fonttype": "none"})
    cols = present + ["none"]
    fig, axes = plt.subplots(1, 2, figsize=(3.45, 1.75), constrained_layout=True)
    for ax, m in zip(axes, ["B1", "B2"]):
        cm = M.confusion(gold[m], preds_lab[m])
        mat = [[cm[g][c] for c in cols] for g in present]
        ax.imshow(mat, cmap="Greys", vmin=0, vmax=max(1, max(max(r) for r in mat)))
        for i, row in enumerate(mat):
            for j, v in enumerate(row):
                ax.text(j, i, str(v), ha="center", va="center", fontsize=6.5,
                        color="white" if v > 0.6 * max(1, max(max(r) for r in mat)) else "black")
        ax.set_xticks(range(len(cols)), [SHORT.get(c, "None")[:4] for c in cols], rotation=0)
        ax.set_yticks(range(len(present)), [SHORT[c][:4] for c in present] if m == "B1" else [""] * len(present))
        ax.set_title(f"{m} (n={n})", fontsize=7)
        ax.tick_params(length=0)
    axes[0].set_ylabel("Reference")
    fig.supxlabel("Prediction (None = abstention or failure)", fontsize=6.5)
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / "confusion.pdf")
    fig.savefig(FIGS / "confusion.svg")
    plt.close(fig)


def main() -> None:
    cases = {c["case_id"]: c for c in json.loads((ROOT / "data/cases/manifest.json").read_text(encoding="utf-8"))}
    cfg = load_json(ROOT / "configs" / "heldout_runs.json", {})
    unlocked = (ROOT / "runs" / "heldout" / "UNLOCK.json").exists()
    preds = load_predictions({m: f"runs/heldout/{rid}" for m, rid in cfg.items()}) if unlocked else {}
    sealed = load_predictions({m: f"runs/sealed/{rid}" for m, rid in cfg.items()}) if not unlocked else {}
    ref_list = load_json(ROOT / "annotations" / "reference_labels.json", [])
    ref = {r["case_id"]: r for r in ref_list}
    final = {c: r["label"] for c, r in ref.items() if r.get("label") in LABELS}
    need = [c for c, x in cases.items() if x["split"] == "evaluation" and x["stratum"] != "order_control"]
    if not unlocked or any(c not in ref or ref[c]["status"] == "pending" for c in need):
        pending("Human reference labels are not final, so no accuracy is reported. Held-out model runs are sealed.",
                sealed or preds, cases)
        return

    strata = {s: sorted(c for c, x in cases.items() if x["split"] == "evaluation" and x["stratum"] == s and c in final)
              for s in ("original", "context_variant", "order_control")}
    excluded = {s: sum(1 for c, x in cases.items() if x["split"] == "evaluation" and x["stratum"] == s
                       and c not in final) for s in strata}
    lab = lambda m, c: (preds[m][c].get("label") if c in preds.get(m, {}) else None)  # noqa: E731
    flag = lambda m, c: (preds["B0"][c]["conflict_flag"] if m == "B0" else  # noqa: E731
                         (None if lab(m, c) is None else lab(m, c) == CONFLICT))
    res: dict = {"strata_n": {s: len(v) for s, v in strata.items()}, "excluded_unlabelled": excluded,
                 "agreement": load_json(ROOT / "annotations" / "agreement.json", {}), "methods": {}}
    for s, ids in strata.items():
        gold = [final[c] for c in ids]
        res.setdefault("support", {})[s] = {lb: sum(1 for g in gold if g == lb) for lb in LABELS}
        for m in ["B0"] + METHODS:
            if m not in preds:
                continue
            r = res["methods"].setdefault(m, {}).setdefault(s, {})
            fl = [flag(m, c) for c in ids]
            r["binary"] = M.binary_conflict(gold, fl)
            r["false_conflict"] = [M.false_conflict_rate(gold, fl, k) for k in ("Valid override",
                                                                                 "Disjoint applicability")]
            if m == "B0":
                continue
            pr = [lab(m, c) for c in ids]
            mf, absent = M.macro_f1(gold, pr)
            r.update(accuracy=M.accuracy(gold, pr), correct=sum(1 for g, p in zip(gold, pr) if g == p), n=len(ids),
                     macro_f1=mf, absent_classes=absent, per_class=M.per_class(gold, pr),
                     confusion=M.confusion(gold, pr),
                     abstained=sum(1 for c in ids if preds[m][c].get("abstained")),
                     failed=sum(1 for c in ids if preds[m][c].get("error")))
            ok = tot = 0
            for c in ids:
                a, t = anchor_validity(cases[c], preds[m][c].get("evidence") or [])
                ok, tot = ok + a, tot + t
            r["anchors"] = {"valid": ok, "cited": tot, "rate": M.safe_div(ok, tot)}
    # paired comparisons (RQ3)
    for m in METHODS:
        if m not in preds:
            continue
        for s, key in (("context_variant", "variant_pairs"), ("order_control", "control_pairs")):
            pairs, changed, same = [], [], []
            for c in strata[s]:
                p = cases[c]["parent_case_id"]
                if p not in final:
                    continue
                t = (final[p], lab(m, p), final[c], lab(m, c))
                pairs.append(t)
                (changed if final[p] != final[c] else same).append(t)
            res["methods"][m][key] = {"all": M.both_correct(pairs), "label_changed": M.both_correct(changed),
                                      "label_same": M.both_correct(same)}
    # paired B2 - B1 on originals, per repository, with a repository-cluster bootstrap
    rows = [{"repo": cases[c]["repo"], "b1": int(lab("B1", c) == final[c]), "b2": int(lab("B2", c) == final[c]),
             "gold": final[c], "p1": lab("B1", c), "p2": lab("B2", c)} for c in strata["original"]]
    diff = lambda s: (sum(r["b2"] - r["b1"] for r in s) / len(s)) if s else None  # noqa: E731
    mf_diff = lambda s: ((M.macro_f1([r["gold"] for r in s], [r["p2"] for r in s])[0] or 0) -  # noqa: E731
                         (M.macro_f1([r["gold"] for r in s], [r["p1"] for r in s])[0] or 0)) if s else None
    res["paired_original"] = {
        "accuracy_diff": diff(rows), "accuracy_diff_ci": M.cluster_bootstrap(rows, diff),
        "macro_f1_diff": mf_diff(rows), "macro_f1_diff_ci": M.cluster_bootstrap(rows, mf_diff),
        "b2_only_correct": sum(1 for r in rows if r["b2"] and not r["b1"]),
        "b1_only_correct": sum(1 for r in rows if r["b1"] and not r["b2"]),
        "per_repo": {rp: {"n": len(v), "b1": sum(r["b1"] for r in v), "b2": sum(r["b2"] for r in v)}
                     for rp, v in sorted(defaultdict(list, {k: [r for r in rows if r["repo"] == k]
                                                            for k in {r["repo"] for r in rows}}).items())}}
    all_ids = [c for s in strata.values() for c in s]
    res["execution"] = execution_table(preds, all_ids)
    EXPORTS.mkdir(parents=True, exist_ok=True)
    w(EXPORTS / "metrics.json", json.dumps(res, indent=1))
    present = [lb for lb in LABELS if res["support"]["original"][lb] > 0]
    confusion_figure({m: [final[c] for c in strata["original"]] for m in ("B1", "B2")},
                     {m: [lab(m, c) for c in strata["original"]] for m in ("B1", "B2")}, present,
                     len(strata["original"]))
    export_tables(res, preds, cases, final, ref, strata)
    write_latex(res)
    print(json.dumps({k: v for k, v in res.items() if k in ("strata_n", "support", "paired_original")}, indent=1))


MNAME = {"B0": "BZero", "B1": "BOne", "B2": "BTwo", "B1R": "BOneR"}
SNAME = {"original": "Orig", "context_variant": "Var", "order_control": "Ctrl"}


def frac(k, n) -> str:
    return f"{k}/{n}"


def write_latex(res: dict) -> None:
    """Numeric macros and two tables for the manuscript; prose is written by the authors around these macros."""
    L = ["% Generated by analysis/results.py from analysis/exports/metrics.json. Do not edit."]
    def mac(name, val):
        L.append(f"\\newcommand{{\\{name}}}{{{val}}}")
    for s, n in res["strata_n"].items():
        mac(f"N{SNAME[s]}Scored", n)
    ag = res["agreement"].get("evaluation", {})
    for s, key in (("original", "Orig"), ("context_variant", "Var")):
        a = ag.get(s, {})
        mac(f"Agree{key}N", a.get("n", "--"))
        mac(f"Agree{key}Obs", fmt(a.get("observed"), pct=True))
        mac(f"Agree{key}Kappa", fmt(a.get("kappa")))
        mac(f"Agree{key}Count", round((a.get("observed") or 0) * (a.get("n") or 0)))
    for m, d in res["methods"].items():
        M_ = MNAME[m]
        for s in ("original", "context_variant", "order_control"):
            r = d[s]
            b = r["binary"]
            mac(f"{M_}{SNAME[s]}TP", b["tp"])
            mac(f"{M_}{SNAME[s]}Flagged", b["flagged"])
            mac(f"{M_}{SNAME[s]}Positives", b["positives"])
            fc = {x["class"]: x for x in r["false_conflict"]}
            mac(f"{M_}{SNAME[s]}FCOverride", frac(fc["Valid override"]["false_conflicts"], fc["Valid override"]["n"]))
            mac(f"{M_}{SNAME[s]}FCDisjoint", frac(fc["Disjoint applicability"]["false_conflicts"],
                                                 fc["Disjoint applicability"]["n"]))
            if m == "B0":
                continue
            mac(f"{M_}{SNAME[s]}Correct", r["correct"])
            mac(f"{M_}{SNAME[s]}Acc", fmt(r["accuracy"], pct=True))
            mac(f"{M_}{SNAME[s]}MacroF", fmt(r["macro_f1"]))
            mac(f"{M_}{SNAME[s]}Abst", r["abstained"])
            mac(f"{M_}{SNAME[s]}Fail", r["failed"])
            mac(f"{M_}{SNAME[s]}AnchorValid", fmt(r["anchors"]["rate"], pct=True))
        if m != "B0":
            for key, nm in (("variant_pairs", "VarPairs"), ("control_pairs", "CtrlPairs")):
                for sub, sn in (("all", ""), ("label_changed", "Changed"), ("label_same", "Same")):
                    x = d[key][sub]
                    mac(f"{M_}{nm}{sn}Both", frac(x["both_correct"], x["n"]))
                    mac(f"{M_}{nm}{sn}Stable", frac(x["same_prediction"], x["n"]))
    p = res["paired_original"]
    mac("DiffAccOrig", fmt(p["accuracy_diff"], pct=True))
    mac("DiffAccOrigLo", fmt(p["accuracy_diff_ci"]["lo"], pct=True))
    mac("DiffAccOrigHi", fmt(p["accuracy_diff_ci"]["hi"], pct=True))
    mac("DiffMacroF", fmt(p["macro_f1_diff"]))
    mac("DiffMacroFLo", fmt(p["macro_f1_diff_ci"]["lo"]))
    mac("DiffMacroFHi", fmt(p["macro_f1_diff_ci"]["hi"]))
    mac("BTwoOnlyCorrect", p["b2_only_correct"])
    mac("BOneOnlyCorrect", p["b1_only_correct"])
    ex = {r[0]: r for r in res["execution"]}
    for m, r in ex.items():
        mac(f"{MNAME[m]}Calls", r[5])
        mac(f"{MNAME[m]}MeanIn", r[6])
        mac(f"{MNAME[m]}MeanOut", r[7])
        mac(f"{MNAME[m]}MeanLat", r[8])
        mac(f"{MNAME[m]}Failures", r[2])
        mac(f"{MNAME[m]}Retries", r[4])
    absent = res["methods"].get("B1", {}).get("original", {}).get("absent_classes", [])
    mac("AbsentOrig", ", ".join(absent) if absent else "none")
    w(GEN / "results.tex", "\n".join(L) + "\n")
    # Table: support
    S = res["support"]
    rows = [f"{['Originals', 'Variants', 'Controls'][i]} & {res['strata_n'][s]} & " +
            " & ".join(str(S[s][lb]) for lb in LABELS) + r" \\" for i, s in enumerate(S)]
    w(GEN / "tab_support.tex", "\n".join([
        r"\begin{table}[t]", r"\caption{Reference labels per stratum (after adjudication)}", r"\label{tab:support}",
        r"\centering\footnotesize\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{lrrrrrr}", r"\toprule",
        r"Stratum & $n$ & Confl. & Overr. & Disj. & Compat. & Insuff. \\", r"\midrule", *rows,
        r"\bottomrule", r"\end{tabular}", r"\end{table}"]) + "\n")
    # Table: methods
    def cell(m, s, k):
        r = res["methods"][m][s]
        return {"acc": f"{r['correct']}/{r['n']}", "mf": fmt(r["macro_f1"])}[k]
    mrows = []
    for m in ("B0", "B1", "B2", "B1R"):
        if m not in res["methods"]:
            continue
        d = res["methods"][m]
        b = d["original"]["binary"]
        fco = {x["class"]: x for x in d["original"]["false_conflict"]}
        fcs = f"{fco['Valid override']['false_conflicts'] + fco['Disjoint applicability']['false_conflicts']}/" \
              f"{fco['Valid override']['n'] + fco['Disjoint applicability']['n']}"
        if m == "B0":
            five = ["--"] * 5
        else:
            five = [cell(m, "original", "acc"), cell(m, "original", "mf"), cell(m, "context_variant", "acc"),
                    f"{d['variant_pairs']['all']['both_correct']}/{d['variant_pairs']['all']['n']}",
                    f"{d['control_pairs']['all']['both_correct']}/{d['control_pairs']['all']['n']}"]
        e = ex.get(m)
        cost = f"{e[5] / max(e[1], 1):.1f} / {e[7]}" if e and m != "B0" else "0 / 0"
        mrows.append(f"{m} & " + " & ".join(five) + f" & {b['tp']}/{b['flagged']} & {fcs} & {cost}" + r" \\")
    w(GEN / "tab_methods.tex", "\n".join([
        r"\begin{table*}[t]", r"\caption{Results on held-out cases. Correct/total; macro-F1 over classes present in the "
        r"reference; pairs count both members correct; conflict flags are true positives/all flags on originals; false "
        r"conflicts are flags on reference overrides and disjoint cases. Cost: mean calls / mean output tokens per case.}",
        r"\label{tab:methods}", r"\centering\footnotesize", r"\begin{tabular}{lcccccccc}", r"\toprule",
        r" & \multicolumn{2}{c}{Originals} & Variants & Variant pairs & Control pairs & Conflict flags & "
        r"False conflicts & Cost \\", r"Method & correct & macro-F1 & correct & both correct & both correct & "
        r"TP/flagged & on overr.+disj. & calls / out tok. \\", r"\midrule", *mrows, r"\bottomrule", r"\end{tabular}",
        r"\end{table*}"]) + "\n")


def export_tables(res, preds, cases, final, ref, strata) -> None:
    """Site/paper tables generated from the same metrics object."""
    S = res["support"]
    tables = []
    cols = ["Stratum", "n"] + [SHORT[lb] for lb in LABELS]
    tables.append({"id": "support", "title": "Reference label support",
                   "caption": "Final human reference labels per stratum (order controls inherit their parent's label).",
                   "columns": cols, "rows": [[s, res["strata_n"][s]] + [S[s][lb] for lb in LABELS] for s in S],
                   "notes": f"Excluded without a final label: {res['excluded_unlabelled']}"})
    mrows = []
    for m in ["B1", "B2", "B1R"]:
        if m not in res["methods"]:
            continue
        for s in ("original", "context_variant", "order_control"):
            r = res["methods"][m][s]
            mrows.append([m, s, r["n"], r["correct"], r["accuracy"], r["macro_f1"], r["abstained"], r["failed"]])
    tables.append({"id": "methods", "title": "Five-class results", "caption": "Accuracy and macro-F1 over classes "
                   "present in the reference; abstentions and failures count as incorrect.",
                   "columns": ["Method", "Stratum", "n", "Correct", "Accuracy", "Macro-F1", "Abstained", "Failed"],
                   "rows": [[a, b, c, d, round(e, 3) if e is not None else None,
                             round(f, 3) if f is not None else None, g, h] for a, b, c, d, e, f, g, h in mrows],
                   "notes": ""})
    brows = []
    for m in ["B0", "B1", "B2", "B1R"]:
        if m not in res["methods"]:
            continue
        r = res["methods"][m]["original"]
        b = r["binary"]
        fc = {x["class"]: x for x in r["false_conflict"]}
        brows.append([m, b["tp"], b["flagged"], b["positives"], b["precision"], b["recall"],
                      f"{fc['Valid override']['false_conflicts']}/{fc['Valid override']['n']}",
                      f"{fc['Disjoint applicability']['false_conflicts']}/{fc['Disjoint applicability']['n']}"])
    tables.append({"id": "binary", "title": "Conflict detection on originals",
                   "caption": "Positive = reference Unresolved conflict. Undefined (empty denominator) shown as a dash.",
                   "columns": ["Method", "TP", "Flagged", "Reference conflicts", "Precision", "Recall",
                               "False conflicts on overrides", "False conflicts on disjoint"],
                   "rows": [[a, b, c, d, round(e, 3) if e is not None else None, round(f, 3) if f is not None else None,
                             g, h] for a, b, c, d, e, f, g, h in brows], "notes": ""})
    prow = []
    for m in ["B1", "B2", "B1R"]:
        if m not in res["methods"]:
            continue
        v, c = res["methods"][m]["variant_pairs"], res["methods"][m]["control_pairs"]
        prow.append([m, f"{v['all']['both_correct']}/{v['all']['n']}",
                     f"{v['label_changed']['both_correct']}/{v['label_changed']['n']}",
                     f"{v['label_same']['both_correct']}/{v['label_same']['n']}",
                     f"{c['all']['both_correct']}/{c['all']['n']}", f"{c['all']['same_prediction']}/{c['all']['n']}"])
    tables.append({"id": "paired", "title": "Paired context results", "caption": "Both-correct counts for "
                   "(original, variant) and (original, order control) pairs; stability counts identical predictions "
                   "whether or not they are correct.",
                   "columns": ["Method", "Variant pairs both correct", "…label changed", "…label same",
                               "Control pairs both correct", "Control pairs same prediction"], "rows": prow,
                   "notes": ""})
    tables.append({"id": "execution", "title": "Execution and cost", "caption": "Per-method totals over all scored "
                   "evaluation cases; means per case.",
                   "columns": ["Method", "Cases", "Failures", "Abstentions", "Retries", "Calls", "Mean input tokens",
                               "Mean output tokens", "Mean latency (s)"], "rows": res["execution"], "notes": ""})
    ag = res["agreement"].get("evaluation", {})
    if ag:
        tables.append({"id": "agreement", "title": "Agreement before adjudication",
                       "caption": "Two independent annotators; Cohen's kappa over the five labels.",
                       "columns": ["Stratum", "n", "Observed agreement", "Cohen's kappa"],
                       "rows": [[s, ag[s]["n"], round(ag[s]["observed"], 3) if ag[s]["observed"] is not None else None,
                                 round(ag[s]["kappa"], 3) if ag[s]["kappa"] is not None else None] for s in ag],
                       "notes": ""})
    TABLES.mkdir(parents=True, exist_ok=True)
    for t in tables:
        with (TABLES / f"{t['id']}.csv").open("w", newline="", encoding="utf-8") as fh:
            cw = csv.writer(fh, lineterminator="\n")
            cw.writerow(t["columns"])
            cw.writerows(t["rows"])
    w(EXPORTS / "results.json", json.dumps({"available": True, "reason": "", "tables": tables,
                                            "figures": [{"id": "confusion", "title": "Confusion matrices on originals",
                                                         "caption": "Rows: reference label; columns: prediction.",
                                                         "path": "figures/confusion.svg"}],
                                            "limitations": LIMITATIONS}, indent=1))
    replay = []
    for cid in sorted(c for s in strata.values() for c in s):
        x = cases[cid]
        r = ref.get(cid) or ref.get(x.get("parent_case_id")) or {}
        def pr(m):
            p = preds.get(m, {}).get(cid)
            if not p:
                return None
            if m == "B0":
                return {"conflict_flag": p["conflict_flag"]}
            return {"label": p.get("label"), "abstained": p.get("abstained"), "explanation": p.get("explanation"),
                    "evidence": p.get("evidence"), "error": p.get("error")}
        pk = x["packet"]
        replay.append({"case_id": cid, "stratum": x["stratum"], "parent_case_id": x["parent_case_id"],
                       "changed_property": x["changed_property"], "repo": x["repo"], "commit": x["commit"],
                       "license": x["license"], "task": x["task"], "task_origin": x["task_origin"],
                       "target_path": x["target_path"], "loaded_set": [p for p in pk["agents_paths"]
                                                                       if _on_chain(p, x["target_path"])],
                       "rule_a": {k: pk["rule_1"][k] for k in ("path", "start_line", "end_line", "heading", "text")},
                       "rule_b": {k: pk["rule_2"][k] for k in ("path", "start_line", "end_line", "heading", "text")},
                       "reference": {"label": final.get(cid), "status": (ref.get(cid) or {}).get("status"),
                                     "annotator_1": (ref.get(cid) or {}).get("a1"),
                                     "annotator_2": (ref.get(cid) or {}).get("a2"),
                                     "adjudication_reason": (ref.get(cid) or {}).get("adjudication_reason")},
                       "predictions": {m: pr(m) for m in ("B0", "B1", "B2")}})
    w(EXPORTS / "replay.json", json.dumps({"available": True, "reason": "", "cases": replay}, indent=1,
                                          ensure_ascii=False))
    w(EXPORTS / "status.json", json.dumps({"version": VERSION, "date": VERSION_DATE, "results_available": True,
                                           "status_label": "Pilot results: small human-labelled sample "
                                                           f"({res['strata_n']['original']} originals)"}, indent=1))


def _on_chain(agents_path: str, target: str) -> bool:
    d = agents_path.rpartition("/")[0]
    t = target.rpartition("/")[0]
    return d == "" or t == d or t.startswith(d + "/")


LIMITATIONS = [
    "Small, challenge-oriented sample from eight repositories; it cannot estimate how often conflicts occur.",
    "Tasks are researcher-authored templates; variants and order controls are constructed material.",
    "Annotators are the paper's authors; one adjudicator.",
    "One declared loading profile (P1) and one quantized local model.",
    "Classification under P1 only; no claim about agent behaviour or code quality.",
]


if __name__ == "__main__":
    main()
