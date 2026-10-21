"""Label-free and profile-determined analysis (docs/analysis_plan.md, addendum A2).

Used because no human reference labels exist for this submission. Nothing here uses or simulates human labels.
Profile-determined (PD) reference: a case whose instruction file is off the target's directory chain must be
"Disjoint applicability" under profile P1; computed from paths only.

Inputs : runs/heldout/<run_id>/predictions.jsonl for configs/heldout_runs.json (after unlock), data/cases/manifest.json
Outputs: analysis/exports/{metrics,results,replay,status}.json, analysis/tables/*.csv, paper/generated/results.tex,
         paper/generated/tab_results.tex, paper/build/figures/labels.{pdf,svg}
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cipher.metrics import LABELS, cohen_kappa, safe_div  # noqa: E402
from cipher.profile import loaded_set  # noqa: E402

EXPORTS, TABLES = ROOT / "analysis" / "exports", ROOT / "analysis" / "tables"
GEN, FIGS = ROOT / "paper" / "generated", ROOT / "paper" / "build" / "figures"
VERSION, VERSION_DATE = "1.0.0", "2026-10-21"
DISJOINT, CONFLICT = "Disjoint applicability", "Unresolved conflict"
MODELS = ["B1", "B2", "B1R"]
SHORT = {"Unresolved conflict": "Conflict", "Valid override": "Override", "Disjoint applicability": "Disjoint",
         "Compatible": "Compatible", "Insufficient evidence": "Insufficient", None: "None"}
MNAME = {"B0": "BZero", "B1": "BOne", "B2": "BTwo", "B1R": "BOneR"}


def w(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def profile_determined(case: dict) -> bool:
    pk = case["packet"]
    chain = loaded_set(case["target_path"], pk["agents_paths"])
    return any(pk[r]["path"] not in chain for r in ("rule_1", "rule_2"))


def load_runs() -> dict[str, dict[str, dict]]:
    if not (ROOT / "runs" / "heldout" / "UNLOCK.json").exists():
        sys.exit("held-out runs are still sealed; run `python -m cipher.unlock_labelfree` first")
    cfg = json.loads((ROOT / "configs" / "heldout_runs.json").read_text(encoding="utf-8"))
    out = {}
    for m, rid in cfg.items():
        f = ROOT / "runs" / "heldout" / rid / "predictions.jsonl"
        out[m] = {json.loads(x)["case_id"]: json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x}
    return out


def fr(k: int, n: int) -> str:
    return f"{k}/{n}"


def main() -> None:
    cases = {c["case_id"]: c for c in json.loads((ROOT / "data/cases/manifest.json").read_text(encoding="utf-8"))
             if c["split"] == "evaluation"}
    P = load_runs()
    lab = lambda m, c: (P[m].get(c) or {}).get("label")  # noqa: E731
    flag = lambda m, c: (P["B0"].get(c) or {}).get("conflict_flag") if m == "B0" else lab(m, c) == CONFLICT  # noqa
    strata = {s: sorted(c for c, x in cases.items() if x["stratum"] == s)
              for s in ("original", "context_variant", "order_control")}
    pd = sorted(c for c, x in cases.items() if profile_determined(x))
    pd_main = [c for c in pd if cases[c]["stratum"] != "order_control"]
    ann = strata["original"] + strata["context_variant"]
    res: dict = {"mode": "label-free (analysis plan addendum A2); no human reference labels",
                 "n": {s: len(v) for s, v in strata.items()}, "pd": {"all": len(pd), "main": len(pd_main),
                 "by_stratum": dict(Counter(cases[c]["stratum"] for c in pd))}, "methods": {}}
    for m in ["B0"] + MODELS:
        r: dict = {}
        r["pd_false_conflicts"] = {"k": sum(1 for c in pd if flag(m, c)), "n": len(pd)}
        r["called_conflict"] = {s: {"k": sum(1 for c in ids if flag(m, c)), "n": len(ids)} for s, ids in strata.items()}
        if m != "B0":
            r["pd_correct_main"] = {"k": sum(1 for c in pd_main if lab(m, c) == DISJOINT), "n": len(pd_main)}
            r["pd_breakdown"] = dict(Counter(SHORT[lab(m, c)] for c in pd_main))
            r["distribution"] = {s: dict(Counter(SHORT[lab(m, c)] for c in ids)) for s, ids in strata.items()}
            ctl = [(cases[c]["parent_case_id"], c) for c in strata["order_control"]]
            r["order_stable"] = {"k": sum(1 for p, c in ctl if lab(m, p) is not None and lab(m, p) == lab(m, c)),
                                 "n": len(ctl)}
            pdc = [(p, c) for p, c in ctl if p in pd]
            r["order_pd_both_correct"] = {"k": sum(1 for p, c in pdc if lab(m, p) == lab(m, c) == DISJOINT),
                                          "n": len(pdc)}
            tv = [c for c in strata["context_variant"] if cases[c]["changed_property"] == "target_path"]
            pv = [c for c in strata["context_variant"] if cases[c]["changed_property"] == "source_placement"]
            par = lambda c: cases[c]["parent_case_id"]  # noqa: E731
            r["target_variants"] = {"correct": sum(1 for c in tv if lab(m, c) == DISJOINT),
                                    "changed": sum(1 for c in tv if lab(m, c) != lab(m, par(c))), "n": len(tv)}
            r["placement_variants"] = {"changed": sum(1 for c in pv if lab(m, c) != lab(m, par(c))), "n": len(pv)}
            r["abstained"] = sum(1 for c in cases if (P[m].get(c) or {}).get("abstained"))
            r["failed"] = sum(1 for c in cases if (P[m].get(c) or {}).get("error") or c not in P[m])
        rs = [P[m][c] for c in cases if c in P[m]]
        att = [a for x in rs for a in x.get("attempts", [])]
        r["execution"] = {"cases": len(cases), "missing": len(cases) - len(rs),
                          "calls": sum(x.get("calls", 0) for x in rs), "retries": sum(x.get("retries", 0) for x in rs),
                          "bad_outputs": sum(1 for a in att if a.get("status") in ("malformed", "schema_violation")),
                          "truncated": sum(1 for a in att if a.get("status") == "truncated"),
                          "api_errors": sum(1 for a in att if a.get("status") == "api_error"),
                          "mean_in": round(sum(x.get("input_tokens", 0) for x in rs) / max(len(rs), 1)),
                          "mean_out": round(sum(x.get("output_tokens", 0) for x in rs) / max(len(rs), 1)),
                          "mean_latency_s": round(sum(x.get("latency_s", 0) for x in rs) / max(len(rs), 1), 1)}
        res["methods"][m] = r
    if "B1R" in P:
        res["methods"]["B1R"]["review_changed"] = {
            "k": sum(1 for c in cases if (P["B1R"].get(c) or {}).get("first_label") not in (None, "Abstain")
                     and P["B1R"][c]["first_label"] != P["B1R"][c].get("label")), "n": len(cases)}
    res["agreement"] = {}
    for a, b in (("B1", "B2"), ("B1", "B1R"), ("B2", "B1R")):
        for s in ("original", "context_variant"):
            ids = [c for c in strata[s] if lab(a, c) and lab(b, c)]
            k = cohen_kappa([lab(a, c) for c in ids], [lab(b, c) for c in ids])
            res["agreement"][f"{a}-{b}:{s}"] = {"n": k["n"], "agree": round(k["observed"] * k["n"]) if k["n"] else 0,
                                                "kappa": k["kappa"]}
    d = res["methods"]
    res["primary"] = {"b2_correct": d["B2"]["pd_correct_main"]["k"], "b1_correct": d["B1"]["pd_correct_main"]["k"],
                      "n": len(pd_main),
                      "b2_only": sum(1 for c in pd_main if lab("B2", c) == DISJOINT != lab("B1", c)),
                      "b1_only": sum(1 for c in pd_main if lab("B1", c) == DISJOINT != lab("B2", c))}
    wrong_b1 = next((c for c in pd_main if lab("B1", c) != DISJOINT), None)
    dis = next((c for c in strata["original"] if c not in pd and lab("B1", c) != lab("B2", c)), None)
    res["illustrative"] = {k: (None if c is None else {"case_id": c, "repo": cases[c]["repo"],
                                                        "relation": cases[c]["relation"],
                                                        **{m: lab(m, c) for m in MODELS},
                                                        "B0": (P["B0"].get(c) or {}).get("conflict_flag")})
                           for k, c in (("first PD case B1 gets wrong", wrong_b1),
                                        ("first non-PD original where B1 and B2 disagree", dis))}
    w(EXPORTS / "metrics.json", json.dumps(res, indent=1))
    figure(P, strata, cases)
    exports(res, P, cases, pd)
    latex(res)
    print(json.dumps({"pd": res["pd"], "primary": res["primary"],
                      "pd_correct": {m: d[m].get("pd_correct_main") for m in MODELS},
                      "called_conflict_orig": {m: d[m]["called_conflict"]["original"] for m in d}}, indent=1))


def figure(P, strata, cases) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Nimbus Roman", "Times", "DejaVu Serif"],
                         "font.size": 7, "svg.fonttype": "none", "pdf.fonttype": 42})
    cats = ["Conflict", "Override", "Disjoint", "Compatible", "Insufficient", "None"]
    shades = ["#1b1b1b", "#555555", "#8c8c8c", "#c4c4c4", "#e6e6e6", "#ffffff"]
    rows = [(m, s) for s in ("original", "context_variant") for m in MODELS]
    fig, ax = plt.subplots(figsize=(3.45, 1.65), constrained_layout=True)
    for i, (m, s) in enumerate(rows):
        cnt = Counter(SHORT[(P[m].get(c) or {}).get("label")] for c in strata[s])
        left = 0
        for cat, col in zip(cats, shades):
            v = cnt.get(cat, 0)
            if v:
                ax.barh(i, v, left=left, color=col, edgecolor="black", linewidth=0.4)
                if v >= 2:
                    ax.text(left + v / 2, i, str(v), ha="center", va="center", fontsize=6,
                            color="white" if col in shades[:2] else "black")
            left += v
    ax.set_yticks(range(len(rows)), [f"{m} {'orig.' if s == 'original' else 'var.'}" for m, s in rows])
    ax.invert_yaxis()
    ax.set_xlabel("Cases (27 originals, 27 variants)")
    ax.set_xlim(0, 27)
    from matplotlib.patches import Patch
    used = {SHORT[(P[m].get(c) or {}).get("label")] for m, s in rows for c in strata[s]}
    fig.legend(handles=[Patch(facecolor=c, edgecolor="black", linewidth=0.4, label=l)
                        for l, c in zip(cats, shades) if l in used],
               ncol=len(used), fontsize=6, loc="outside upper center", frameon=False)
    FIGS.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGS / "labels.pdf")
    fig.savefig(FIGS / "labels.svg")
    plt.close(fig)


def exports(res, P, cases, pd) -> None:
    d = res["methods"]
    rows = []
    for m in ["B0"] + MODELS:
        x = d[m]
        e = x["execution"]
        rows.append([m, fr(x["pd_correct_main"]["k"], x["pd_correct_main"]["n"]) if m != "B0" else None,
                     fr(x["pd_false_conflicts"]["k"], x["pd_false_conflicts"]["n"]),
                     fr(x["called_conflict"]["original"]["k"] + x["called_conflict"]["context_variant"]["k"], 54),
                     fr(x["order_stable"]["k"], x["order_stable"]["n"]) if m != "B0" else None,
                     fr(x["target_variants"]["changed"], x["target_variants"]["n"]) if m != "B0" else None,
                     fr(x["placement_variants"]["changed"], x["placement_variants"]["n"]) if m != "B0" else None,
                     round(e["calls"] / e["cases"], 2), e["mean_out"]])
    cols = ["Method", "Profile-determined correct (originals + variants)", "False conflicts on profile-determined",
            "Called 'Unresolved conflict' (originals + variants)", "Order controls: same prediction",
            "Target-path variants: prediction changed", "Placement variants: prediction changed", "Calls per case",
            "Mean output tokens"]
    ag = [[k.split(":")[0], k.split(":")[1], v["n"], v["agree"], None if v["kappa"] is None else round(v["kappa"], 3)]
          for k, v in res["agreement"].items()]
    dist = [[m, s] + [d[m]["distribution"][s].get(SHORT[lb], 0) for lb in LABELS] + [d[m]["distribution"][s].get(
        "None", 0)] for m in MODELS for s in ("original", "context_variant", "order_control")]
    ex = [[m, e["cases"], e["missing"], d[m].get("failed", 0), d[m].get("abstained", 0), e["bad_outputs"],
           e["truncated"], e["api_errors"], e["retries"], e["calls"], e["mean_in"], e["mean_out"], e["mean_latency_s"]]
          for m, e in ((m, d[m]["execution"]) for m in ["B0"] + MODELS)]
    tables = [
        {"id": "summary", "title": "Results without human labels", "caption": "Profile-determined (PD) cases have one "
         "instruction file off the target's directory chain, so P1 fixes the label (Disjoint applicability); B2 "
         "computes this in code. Other columns need no reference label.", "columns": cols, "rows": rows,
         "notes": f"PD cases: {res['pd']['main']} originals and variants, {res['pd']['all']} including order controls."},
        {"id": "distribution", "title": "Predicted labels per method and stratum", "caption": "Counts of predicted "
         "labels; None = abstention or failure. Not accuracy.", "columns": ["Method", "Stratum"] +
         [SHORT[lb] for lb in LABELS] + ["None"], "rows": dist, "notes": ""},
        {"id": "agreement", "title": "Agreement between methods", "caption": "Agreement between systems, not with "
         "a reference.", "columns": ["Pair", "Stratum", "n", "Same label", "Cohen's kappa"], "rows": ag, "notes": ""},
        {"id": "execution", "title": "Execution and cost", "caption": "Latency is not comparable across methods (shared "
         "GPU and a runtime patch update during the runs).", "columns": ["Method", "Cases", "Missing", "Failures",
         "Abstentions", "Malformed attempts", "Truncated attempts", "API errors", "Retries", "Calls",
         "Mean input tokens", "Mean output tokens", "Mean latency (s)"], "rows": ex, "notes": ""}]
    TABLES.mkdir(parents=True, exist_ok=True)
    for t in tables:
        with (TABLES / f"{t['id']}.csv").open("w", newline="", encoding="utf-8") as fh:
            cw = csv.writer(fh, lineterminator="\n")
            cw.writerow(t["columns"])
            cw.writerows(t["rows"])
    lim = ["No human reference labels: accuracy is reported only where profile P1 fixes the label (26 cases).",
           "B2 computes path applicability in code, so its profile-determined accuracy reflects structure, not "
           "semantic judgement.", "Small, challenge-oriented sample from eight repositories; tasks are researcher-"
           "authored; variants and controls are constructed.", "One declared profile and one quantized local model."]
    w(EXPORTS / "results.json", json.dumps({"available": True, "reason": "", "tables": tables, "figures": [
        {"id": "labels", "title": "Predicted labels", "caption": "Predicted-label distribution per method on originals "
         "and variants (not accuracy).", "path": "figures/labels.svg"}], "limitations": lim}, indent=1))
    replay = []
    for cid in sorted(cases):
        x = cases[cid]
        pk = x["packet"]
        chain = loaded_set(x["target_path"], pk["agents_paths"])
        def pr(m):
            p = P[m].get(cid)
            if not p:
                return None
            if m == "B0":
                return {"conflict_flag": p["conflict_flag"]}
            return {"label": p.get("label"), "abstained": p.get("abstained"), "explanation": p.get("explanation"),
                    "evidence": p.get("evidence"), "error": p.get("error")}
        replay.append({"case_id": cid, "stratum": x["stratum"], "parent_case_id": x["parent_case_id"],
                       "changed_property": x["changed_property"], "repo": x["repo"], "commit": x["commit"],
                       "license": x["license"], "task": x["task"], "task_origin": x["task_origin"],
                       "target_path": x["target_path"], "loaded_set": chain,
                       "rule_a": {k: pk["rule_1"][k] for k in ("path", "start_line", "end_line", "heading", "text")},
                       "rule_b": {k: pk["rule_2"][k] for k in ("path", "start_line", "end_line", "heading", "text")},
                       "reference": {"label": DISJOINT if cid in pd else None,
                                     "status": "profile-determined (computed from paths, not a human label)"
                                     if cid in pd else "no reference label (human annotation not performed)",
                                     "annotator_1": None, "annotator_2": None, "adjudication_reason": None},
                       "predictions": {m: pr(m) for m in ("B0", "B1", "B2")}})
    w(EXPORTS / "replay.json", json.dumps({"available": True, "reason": "", "cases": replay}, indent=1,
                                          ensure_ascii=False))
    w(EXPORTS / "status.json", json.dumps({"version": VERSION, "date": VERSION_DATE, "results_available": True,
                                           "status_label": "Preliminary results without human labels "
                                                           "(profile-determined subset and label-free measures)"},
                                          indent=1))


def latex(res) -> None:
    d = res["methods"]
    L = ["% Generated by analysis/labelfree.py from analysis/exports/metrics.json. Do not edit.", r"\resultstrue"]
    mac = lambda n, v: L.append(f"\\newcommand{{\\{n}}}{{{v}}}")  # noqa: E731
    mac("NPD", res["pd"]["all"])
    mac("NPDMain", res["pd"]["main"])
    for s, k in (("original", "Orig"), ("context_variant", "Var"), ("order_control", "Ctrl")):
        mac(f"NPD{k}", res["pd"]["by_stratum"].get(s, 0))
    for m, x in d.items():
        M = MNAME[m]
        mac(f"{M}PDFalseConf", x["pd_false_conflicts"]["k"])
        cc = x["called_conflict"]
        mac(f"{M}CalledConfOrig", cc["original"]["k"])
        mac(f"{M}CalledConfVar", cc["context_variant"]["k"])
        mac(f"{M}CalledConfAnn", cc["original"]["k"] + cc["context_variant"]["k"])
        e = x["execution"]
        mac(f"{M}CallsPerCase", f"{e['calls'] / e['cases']:.2f}")
        mac(f"{M}MeanIn", e["mean_in"])
        mac(f"{M}MeanOut", e["mean_out"])
        mac(f"{M}BadOutputs", e["bad_outputs"])
        mac(f"{M}Retries", e["retries"])
        if m == "B0":
            continue
        mac(f"{M}PDCorrect", x["pd_correct_main"]["k"])
        for k, v in sorted(x["pd_breakdown"].items()):
            mac(f"{M}PDPred{k}", v)
        mac(f"{M}OrderStable", x["order_stable"]["k"])
        mac(f"{M}OrderPDBoth", x["order_pd_both_correct"]["k"])
        mac(f"{M}TVCorrect", x["target_variants"]["correct"])
        mac(f"{M}TVChanged", x["target_variants"]["changed"])
        mac(f"{M}PVChanged", x["placement_variants"]["changed"])
        mac(f"{M}Abstained", x["abstained"])
        mac(f"{M}Failed", x["failed"])
        for lb in ("Conflict", "Override", "Disjoint", "Compatible", "Insufficient", "None"):
            mac(f"{M}DistOrig{lb}", x["distribution"]["original"].get(lb, 0))
            mac(f"{M}DistVar{lb}", x["distribution"]["context_variant"].get(lb, 0))
    if "review_changed" in d.get("B1R", {}):
        mac("BOneRReviewChanged", d["B1R"]["review_changed"]["k"])
    for k, v in res["agreement"].items():
        pair, s = k.split(":")
        nm = "Agree" + pair.replace("-", "").replace("B1R", "BOneR").replace("B1", "BOne").replace("B2", "BTwo") + \
             ("Orig" if s == "original" else "Var")
        mac(nm + "N", v["n"])
        mac(nm + "Same", v["agree"])
        mac(nm + "Kappa", "--" if v["kappa"] is None else f"{v['kappa']:.2f}")
    p = res["primary"]
    mac("PrimaryBTwoOnly", p["b2_only"])
    mac("PrimaryBOneOnly", p["b1_only"])
    w(GEN / "results.tex", "\n".join(L) + "\n")
    row = lambda m: (f"{m} & " + (f"{d[m]['pd_correct_main']['k']}/{res['pd']['main']}" if m != "B0" else "--") +  # noqa
                     f" & {d[m]['pd_false_conflicts']['k']}/{res['pd']['all']} & "
                     f"{d[m]['called_conflict']['original']['k'] + d[m]['called_conflict']['context_variant']['k']}/54"
                     + (f" & {d[m]['order_stable']['k']}/{d[m]['order_stable']['n']} & "
                        f"{d[m]['target_variants']['changed']}/{d[m]['target_variants']['n']} & "
                        f"{d[m]['placement_variants']['changed']}/{d[m]['placement_variants']['n']}"
                        if m != "B0" else " & -- & -- & --") +
                     f" & {d[m]['execution']['calls'] / d[m]['execution']['cases']:.2f} / "
                     f"{d[m]['execution']['mean_out']}" + r" \\")
    w(GEN / "tab_results.tex", "\n".join([
        r"\begin{table*}[t]",
        r"\caption{Held-out results without human labels. PD: profile-determined cases (5 mined originals and 16 "
        r"constructed target-path variants; 26 with the 5 order controls), whose correct label under P1 is "
        r"\emph{Disjoint applicability} because an instruction file is off the target's chain (B2 computes this in "
        r"code). Other columns need no reference. B0 outputs only a conflict flag. Single run per arm; repeat "
        r"variation is discussed in the text. Cost: mean calls / mean output tokens per case.}",
        r"\label{tab:results}", r"\centering\footnotesize", r"\begin{tabular}{lccccccc}", r"\toprule",
        r" & PD correct & False conflicts & Called conflict & Order controls & \multicolumn{2}{c}{Prediction changed "
        r"in variants} & Cost \\ \cmidrule(lr){6-7}",
        r"Method & (orig.+var.) & on PD (all) & (orig.+var.) & same prediction & target path & placement & "
        r"calls / tokens \\", r"\midrule", *[row(m) for m in ["B0"] + MODELS], r"\bottomrule", r"\end{tabular}",
        r"\end{table*}"]) + "\n")


if __name__ == "__main__":
    main()
