"""Case construction: originals, context-changing variants, answer-preserving order controls, evidence packets.

Run `python -m cipher.cases` to rebuild `data/cases/manifest.json` deterministically from the stored snapshots.
Nothing here assigns a reference label; labels come only from human annotators.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path

from .acquire import ROOT, load, verify
from .candidates import Candidate, inventory, salient, select, topics
from .mdparse import Unit, section_text, split_lines, units
from .profile import PROFILE_ID, PROFILE_TEXT, depth, file_dir, is_ancestor_dir, loaded_set, relation

SEED = 20261021
K_PER_REPO = 4
N_CALIBRATION_REPOS = 2
N_EVALUATION_REPOS = 8
MIN_PAIRS, MIN_CROSS_FILE = 4, 2
CASES_DIR = ROOT / "data" / "cases"

CODE_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rs", ".java", ".kt", ".cs", ".cpp", ".cc", ".c",
            ".h", ".hpp", ".rb", ".php", ".swift", ".scala", ".vue", ".svelte"}
DOC_EXT = {".md", ".mdx", ".rst"}

DEPENDENCY = re.compile(r"dependenc|lockfile|\binstall\b|`(?:uv|pnpm|yarn|bun|poetry|cargo) add|`npm (?:i|install)|"
                        r"`pip install|package manager|runtime/package", re.I)
TASKS = [  # (trigger topics or terms, template). Researcher-authored, neutral wording.
    ({"formatting", "indent", "tab", "space"}, "Add a new helper function to `{t}`."),
    ({"generated_code", "generated", "codegen", "golden"}, "Change the behaviour implemented in `{t}`."),
    ({"logging_errors", "logging", "logger", "tracing"}, "Add error handling and logging to one function in `{t}`."),
    ({"testing", "linting_typing", "vcs", "test", "lint", "commit", "e2e", "mypy", "tsc", "`pnpm", "`uv", "`yarn",
      "`pixi", "`npm", "`bun", "`cargo", "`make", "`just"},
     "Make a small fix in `{t}` and complete the checks this change requires before committing."),
]
DOC_TASK = "Revise one section of `{t}` and complete the checks this change requires."
DEP_TASK = "Add a new third-party dependency used by `{t}` and complete the checks this change requires."
DEFAULT_TASK = "Make a small behaviour change in `{t}`."
NON_TARGET_NAMES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "CHANGELOG.md", "LICENSE", "LICENSE.md"}

PRECEDENCE_SCAN = re.compile(
    r"AGENTS\.md|overrid|precedence|supersed|take[s]? priority|higher priority|root (?:guide|instruction|rule|file)|"
    r"parent (?:guide|instruction|file)|nested|(?:this|the) (?:file|directory|folder|package)(?:'s)? "
    r"(?:rules|instructions|guidelines)|applies (?:only|to)", re.I)


def opaque(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:8]


def task_for(c: Candidate, target: str) -> str:
    if ext(target) in DOC_EXT:
        return DOC_TASK.format(t=target)
    if DEPENDENCY.search(c.a.text) or DEPENDENCY.search(c.b.text):
        return DEP_TASK.format(t=target)
    keys = set(c.shared_topics) | {s.lstrip("`") for s in salient(c.a.text) & salient(c.b.text)} | \
        (salient(c.a.text) & salient(c.b.text))
    for trig, tmpl in TASKS:
        if keys & trig:
            return tmpl.format(t=target)
    return DEFAULT_TASK.format(t=target)


def ext(p: str) -> str:
    m = re.search(r"\.[^./]+$", p)
    return m.group(0).lower() if m else ""


def pick_target(tree: list[str], under: str, rng: random.Random, exclude_under: str | None = None,
                docs: bool = False) -> str | None:
    """A real file under directory `under` (not under `exclude_under`), preferring code files at minimal depth."""
    pool = [p for p in tree if is_ancestor_dir(under, file_dir(p)) and p.split("/")[-1] not in NON_TARGET_NAMES
            and (exclude_under is None or not is_ancestor_dir(exclude_under, file_dir(p)))
            and not any(part.startswith((".", "_")) or part in {"fixtures", "testdata", "snapshots", "vendor"}
                        for part in p.split("/")[:-1])]
    for exts in ((DOC_EXT if docs else CODE_EXT), CODE_EXT | DOC_EXT):
        cand = [p for p in pool if ext(p) in exts]
        if cand:
            m = min(depth(file_dir(p)) for p in cand)
            shallow = sorted(p for p in cand if depth(file_dir(p)) <= m + 1)
            return rng.choice(shallow)
    return None


def rule_record(u: Unit, content: str) -> dict:
    s_first, s_last, s_text = section_text(content, u.start_line, u.end_line)
    return {"path": u.path, "start_line": u.start_line, "end_line": u.end_line, "heading": u.heading,
            "text": "\n".join(split_lines(content)[u.start_line - 1:u.end_line]),
            "section_first_line": s_first, "section_last_line": s_last, "section_text": s_text}


def precedence_lines(files: dict[str, str], paths: list[str], skip: set[tuple[str, int]]) -> list[dict]:
    out = []
    for p in paths:
        in_fence = False
        for i, line in enumerate(split_lines(files[p]), start=1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if not in_fence and line.strip() and (p, i) not in skip and PRECEDENCE_SCAN.search(line):
                out.append({"path": p, "line": i, "text": line.strip()[:300]})
    return out[:15]


def packet(case_files: dict[str, str], agents_paths: list[str], target: str, r1: dict, r2: dict) -> dict:
    span_lines = {(r["path"], ln) for r in (r1, r2) for ln in range(r["start_line"], r["end_line"] + 1)}
    scan = sorted(set(loaded_set(target, agents_paths)) | {r1["path"], r2["path"]},
                  key=lambda p: (depth(file_dir(p)), p))
    return {"agents_paths": sorted(agents_paths, key=lambda p: (depth(file_dir(p)), p)),
            "rule_1": r1, "rule_2": r2,
            "scope_statements": precedence_lines(case_files, scan, span_lines),
            "full_files": {p: case_files[p] for p in sorted({r1["path"], r2["path"]})}}


def relocate(files: dict[str, str], u: Unit, dest: str) -> tuple[dict[str, str], Unit, dict]:
    """Move unit u's lines from its file to the end of `dest`, under a copy of its original heading.
    Returns the modified files, the relocated unit, and a line-shift map for the origin file."""
    files = dict(files)
    src_lines = split_lines(files[u.path])
    moved = src_lines[u.start_line - 1:u.end_line]
    files[u.path] = "\n".join(src_lines[:u.start_line - 1] + src_lines[u.end_line:])
    dest_lines = split_lines(files[dest])
    while dest_lines and not dest_lines[-1].strip():
        dest_lines.pop()
    heading = u.heading_path[-1] if u.heading_path else "Relocated instruction"
    block = ["", f"## {heading}", ""]
    start = len(dest_lines) + len(block) + 1
    dest_lines += block + moved
    files[dest] = "\n".join(dest_lines) + "\n"
    new_u = Unit(dest, start, start + len(moved) - 1, u.text, [heading], u.kind)
    shift = {"origin": u.path, "removed_from": u.start_line, "removed_count": len(moved)}
    return files, new_u, shift


def shifted(u: Unit, shift: dict) -> Unit:
    if u.path == shift["origin"] and u.start_line > shift["removed_from"]:
        n = shift["removed_count"]
        return Unit(u.path, u.start_line - n, u.end_line - n, u.text, u.heading_path, u.kind)
    return u


def build_repo_cases(snap: dict, tree: list[str], split: str, prefix: str, rng: random.Random) -> list[dict]:
    files = {f["path"]: f["content"] for f in snap["agents_files"]}
    agents_paths = list(files)
    ubf = {p: units(p, c) for p, c in files.items()}
    chosen = select(inventory(ubf), K_PER_REPO, rng)
    out = []
    for n, c in enumerate(chosen, start=1):
        a, b = (c.a, c.b) if rng.random() < 0.5 else (c.b, c.a)  # presentation order is randomised
        rel = relation(a.path, b.path)
        docs_task = "docs" in c.shared_topics
        variant = None
        if rel == "ancestor_descendant":
            deep, shallow = (a, b) if depth(file_dir(a.path)) > depth(file_dir(b.path)) else (b, a)
            target = pick_target(tree, file_dir(deep.path), rng, docs=docs_task)
            alt = pick_target(tree, file_dir(shallow.path), rng, exclude_under=file_dir(deep.path), docs=docs_task)
            if alt:
                variant = {"changed_property": "target_path", "target_path": alt,
                           "description": f"Target moved from {target} to {alt}, outside {file_dir(deep.path)}/; "
                                          "files and rule wording unchanged."}
        elif rel == "unrelated":
            act, inact = (a, b) if rng.random() < 0.5 else (b, a)
            target = pick_target(tree, file_dir(act.path), rng, docs=docs_task)
            variant = {"changed_property": "source_placement", "move": inact, "dest": "AGENTS.md",
                       "description": f"Lines {inact.start_line}-{inact.end_line} of {inact.path} relocated to the end "
                                      "of the root AGENTS.md under a copy of their heading; wording unchanged."}
        else:  # same_file
            d = file_dir(a.path)
            nested = sorted(p for p in agents_paths if p != a.path and is_ancestor_dir(d, file_dir(p)))
            if d == "" and nested:
                dest = rng.choice(nested)
                target = pick_target(tree, file_dir(dest), rng, docs=docs_task)
            else:
                dest = "AGENTS.md" if d != "" else None
                target = pick_target(tree, d, rng, docs=docs_task)
            if dest:
                variant = {"changed_property": "source_placement", "move": b, "dest": dest,
                           "description": f"Lines {b.start_line}-{b.end_line} of {b.path} relocated to the end of "
                                          f"{dest} under a copy of their heading; wording unchanged."}
        if target is None:
            continue
        base_id = f"{prefix}{n:02d}"
        task = task_for(c, target)
        orig = {
            "case_id": base_id, "split": split, "stratum": "original", "parent_case_id": None,
            "changed_property": None, "transformation": None,
            "repo": snap["repo"], "commit": snap["commit"], "license": snap["license"],
            "family_id": f"{snap['repo']}#{n}", "relation": rel, "retrieval_score": c.score,
            "retrieval_signals": c.signals, "task": task, "task_origin": "researcher-authored template",
            "target_path": target, "profile_id": PROFILE_ID,
            "packet": packet(files, agents_paths, target, rule_record(a, files[a.path]), rule_record(b, files[b.path])),
        }
        out.append(orig)
        if variant is None:
            continue
        if variant["changed_property"] == "target_path":
            v_files, v_a, v_b, v_target = files, a, b, variant["target_path"]
            v_task = task.replace(f"`{target}`", f"`{v_target}`")
        else:
            v_files, moved_u, shift = relocate(files, variant["move"], variant["dest"])
            v_a = moved_u if variant["move"] is a else shifted(a, shift)
            v_b = moved_u if variant["move"] is b else shifted(b, shift)
            v_target, v_task = target, task
        out.append({
            **{k: orig[k] for k in ("split", "repo", "commit", "license", "family_id", "relation", "profile_id")},
            "case_id": base_id + "v", "stratum": "context_variant", "parent_case_id": base_id,
            "changed_property": variant["changed_property"], "transformation": variant["description"],
            "retrieval_score": c.score, "retrieval_signals": c.signals,
            "task": v_task, "task_origin": "researcher-authored template", "target_path": v_target,
            "packet": packet(v_files, agents_paths, v_target, rule_record(v_a, v_files[v_a.path]),
                             rule_record(v_b, v_files[v_b.path])),
        })
    return out


def order_control(orig: dict) -> dict:
    p = dict(orig["packet"])
    p["rule_1"], p["rule_2"] = orig["packet"]["rule_2"], orig["packet"]["rule_1"]
    return {**orig, "case_id": orig["case_id"] + "c", "stratum": "order_control", "parent_case_id": orig["case_id"],
            "changed_property": "evidence_order",
            "transformation": "Instruction 1 and Instruction 2 swapped in presentation; nothing else changed.",
            "packet": p}


def case_hash(case: dict) -> str:
    keys = ("repo", "commit", "task", "target_path", "profile_id", "packet")
    return hashlib.sha256(json.dumps({k: case[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def main() -> None:
    log = json.loads((ROOT / "data" / "acquisition_log.json").read_text(encoding="utf-8"))
    selection = {"seed": SEED, "rule": f"repos in seeded frame order that are snapshot-eligible and yield >= "
                 f"{MIN_PAIRS} candidate pairs with >= {MIN_CROSS_FILE} across files; first "
                 f"{N_CALIBRATION_REPOS} -> calibration, next {N_EVALUATION_REPOS} -> evaluation", "repos": []}
    calib, evalr = [], []
    for e in log["tried"]:
        if e["status"] != "eligible":
            selection["repos"].append({"repo": e["repo"], "position": e["position"], "decision": "excluded",
                                       "reasons": e["reasons"]})
            continue
        snap, tree = load(e["repo"])
        errs = verify(snap)
        ubf = {f["path"]: units(f["path"], f["content"]) for f in snap["agents_files"]}
        inv = inventory(ubf)
        cross = sum(1 for c in inv if c.relation != "same_file")
        reasons = errs + ([f"only {len(inv)} candidate pairs ({cross} across files)"]
                          if len(inv) < MIN_PAIRS or cross < MIN_CROSS_FILE else [])
        if reasons:
            decision = "excluded"
        elif len(calib) < N_CALIBRATION_REPOS:
            decision = "calibration"
            calib.append(e["repo"])
        elif len(evalr) < N_EVALUATION_REPOS:
            decision = "evaluation"
            evalr.append(e["repo"])
        else:
            decision = "reserve (not used)"
        selection["repos"].append({"repo": e["repo"], "position": e["position"], "decision": decision,
                                   "commit": snap["commit"], "candidate_pairs": len(inv), "cross_file_pairs": cross,
                                   "reasons": reasons})
    cases = []
    for i, repo in enumerate(calib):
        snap, tree = load(repo)
        cases += build_repo_cases(snap, tree, "calibration", f"K{i + 1}", random.Random(f"{SEED}:{repo}"))
    for i, repo in enumerate(evalr):
        snap, tree = load(repo)
        cases += build_repo_cases(snap, tree, "evaluation", f"E{i + 1}", random.Random(f"{SEED}:{repo}"))
    cases += [order_control(c) for c in cases if c["stratum"] == "original" and c["split"] == "evaluation"]
    for c in cases:
        c["case_sha256"] = case_hash(c)
    cases.sort(key=lambda c: c["case_id"])
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    (CASES_DIR / "manifest.json").write_text(json.dumps(cases, indent=1, ensure_ascii=False), encoding="utf-8")
    (CASES_DIR / "selection_log.json").write_text(json.dumps(selection, indent=1), encoding="utf-8")
    counts = {}
    for c in cases:
        counts[(c["split"], c["stratum"])] = counts.get((c["split"], c["stratum"]), 0) + 1
    print("calibration repos:", calib)
    print("evaluation repos:", evalr)
    print({f"{k[0]}/{k[1]}": v for k, v in sorted(counts.items())})


if __name__ == "__main__":
    main()
