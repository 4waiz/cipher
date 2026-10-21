"""Comparison arms.

B0  pairwise adaptation of Ruleherd v0.1.3 (MIT, github.com/princejain756/ruleherd, commit 94559fc6) contradiction
    heuristics: binary conflict flag only.
B1  direct contextual model: one call, the complete evidence packet, the full profile and the label guidance.
B1R equal-call control: B1 followed by one self-review call over the same evidence (two calls, like B2 at most).
B2  CIPHER structured pipeline: one extraction call (instruction representation + conditional applicability +
    explicit priority statements), deterministic directory ancestry and depth precedence, and one incompatibility call
    only when both instructions remain active. Same model and evidence as B1.
"""

from __future__ import annotations

import re
from pathlib import Path

from .llm import CallResult, ModelConfig, chat
from .profile import PROFILE_TEXT, file_dir, loaded_set, structural_winner

LABELS = ["Unresolved conflict", "Valid override", "Disjoint applicability", "Compatible", "Insufficient evidence"]
PROMPTS = Path(__file__).resolve().parents[2] / "configs" / "prompts"


def prompt(name: str) -> str:
    text = (PROMPTS / f"{name}.txt").read_text(encoding="utf-8")
    return text.replace("{PROFILE}", PROFILE_TEXT.strip()).replace(
        "{GUIDANCE}", (PROMPTS / "common_guidance.txt").read_text(encoding="utf-8").strip())


def numbered(text: str, first: int) -> str:
    return "\n".join(f"{first + i:>5} | {ln}" for i, ln in enumerate(text.split("\n")))


def render_packet(case: dict) -> str:
    """The evidence packet given to every model arm. Contains no case ID, stratum, label, or transformation note."""
    pk = case["packet"]
    parts = [f"Repository: {case['repo']} at commit {case['commit']}",
             f"Task: {case['task']}",
             f"Target file: {case['target_path']}",
             "AGENTS.md files in the repository:\n" + "\n".join(f"  - {p}" for p in pk["agents_paths"])]
    for n in (1, 2):
        r = pk[f"rule_{n}"]
        lines = f"{r['start_line']}" + (f"-{r['end_line']}" if r["end_line"] > r["start_line"] else "")
        parts.append(f"Instruction {n}: {r['path']} lines {lines} (heading: {r['heading'] or 'none'})\n"
                     f"Quoted instruction:\n{numbered(r['text'], r['start_line'])}\n"
                     f"Surrounding section ({r['path']} lines {r['section_first_line']}-{r['section_last_line']}):\n"
                     f"{numbered(r['section_text'], r['section_first_line'])}")
    if pk["scope_statements"]:
        parts.append("Scope and precedence statements found in the loaded files:\n" +
                     "\n".join(f"  {s['path']}:{s['line']} | {s['text']}" for s in pk["scope_statements"]))
    else:
        parts.append("Scope and precedence statements found in the loaded files: none")
    return "\n\n".join(parts)


# ---------------------------------------------------------------- B0
TOPIC_PAIRS = [
    ("package manager", re.compile(r"\bnpm (?:run|install|ci|test|publish|exec|i)\b", re.I),
     re.compile(r"\b(?:pnpm|yarn|bun) (?:run|install|add|test|dlx|exec|i|remove|update|create)\b", re.I)),
    ("test runner", re.compile(r"\bjest\b", re.I), re.compile(r"\b(?:vitest|mocha)\b", re.I)),
    ("indentation", re.compile(r"\bindent\w*[^.\n]{0,30}\btabs?\b|\btabs?\b[^.\n]{0,30}\bindent\w*", re.I),
     re.compile(r"\bindent\w*[^.\n]{0,30}\bspaces?\b|\bspaces?\b[^.\n]{0,30}\bindent\w*", re.I)),
    ("module system", re.compile(r"\b(?:esm|es modules|\"type\"\s*:\s*\"module\"|import\s+[\w*{}\s,]+\s+from\s+['\"])",
                                 re.I), re.compile(r"\b(?:commonjs|cjs|require\s*\()", re.I)),
    ("formatter", re.compile(r"\bprettier\b", re.I), re.compile(r"\b(?:biome|eslint --fix|standardjs)\b", re.I)),
]
NEGATED = re.compile(r"\b(?:never|don't|do not|avoid|no)\b", re.I)
INSTEAD_TAIL = re.compile(r"\b(?:instead of|rather than)\s+[^.,;\n]+", re.I)
TOPIC_RE = re.compile(r"\b(commit|push|delete|merge|rebase|sudo|console\.log|secrets?|api keys?)\b", re.I)
CLAUSE_SPLIT = re.compile(r"\.(?=\s|$)|;|,\s*(?:and|but)\b", re.I)
NEG_POL = re.compile(r"\bnever\b|\bdon't\b|\bdo not\b|\bno \w+ing\b|\bmustn'?t\b|\bmust not\b|\bshouldn'?t\b|"
                     r"\bshould not\b|\bcan'?t\b|\bcannot\b|\bwon'?t\b", re.I)
POS_POL = re.compile(r"\balways\b|\bmust\b(?!\s*not)", re.I)


def _strip_code(text: str) -> str:
    return re.sub(r"^ {0,3}```[^\n]*\n[\s\S]*?^ {0,3}```", "", text, flags=re.M)


def b0(case: dict) -> dict:
    """Ruleherd's checks restricted to the two spans of one case. Like Ruleherd, a flag needs different files."""
    pk = case["packet"]
    r1, r2 = pk["rule_1"], pk["rule_2"]
    if r1["path"] == r2["path"]:
        return {"conflict_flag": False, "topic": None, "note": "same file: Ruleherd only compares different files"}
    t1, t2 = _strip_code(r1["text"]), _strip_code(r2["text"])
    for topic, a_re, b_re in TOPIC_PAIRS:
        def hits(t: str) -> tuple[bool, bool]:
            a = b = False
            for raw in CLAUSE_SPLIT.split(t):
                clause = INSTEAD_TAIL.sub("", raw)
                if NEGATED.search(clause):
                    continue
                a |= bool(a_re.search(clause) and not b_re.search(clause))
                b |= bool(b_re.search(clause) and not a_re.search(clause))
            return a, b
        (a1, b1_), (a2, b2_) = hits(t1), hits(t2)
        if (a1 and b2_) or (b1_ and a2):
            return {"conflict_flag": True, "topic": topic, "note": "TOPIC_PAIRS"}

    def stances(t: str) -> set[tuple[str, bool]]:
        out = set()
        for clause in CLAUSE_SPLIT.split(t):
            neg, pos = bool(NEG_POL.search(clause)), bool(POS_POL.search(clause))
            if neg == pos:
                continue
            for m in TOPIC_RE.finditer(clause):
                out.add((m.group(1).lower().rstrip("s"), pos))
        return out

    s1, s2 = stances(t1), stances(t2)
    for topic, pol in s1:
        if (topic, not pol) in s2:
            return {"conflict_flag": True, "topic": topic + " policy", "note": "polarity"}
    return {"conflict_flag": False, "topic": None, "note": "no rule fired"}


# ---------------------------------------------------------------- B1 / B1R
ANSWER_SCHEMA = {
    "type": "object",
    "properties": {"label": {"type": "string", "enum": LABELS + ["Abstain"]},
                   "explanation": {"type": "string"},
                   "evidence": {"type": "array", "items": {"type": "string"}}},
    "required": ["label", "explanation", "evidence"],
}


def _answer(res: CallResult, calls: list[CallResult]) -> dict:
    out = {"calls": len(calls), "input_tokens": sum(c.input_tokens for c in calls),
           "output_tokens": sum(c.output_tokens for c in calls), "latency_s": round(sum(c.latency_s for c in calls), 2),
           "retries": sum(len(c.attempts) - 1 for c in calls), "attempts": [a for c in calls for a in c.attempts]}
    if not res.ok:
        return {**out, "label": None, "abstained": False, "error": res.error, "explanation": None, "evidence": []}
    d = res.data
    return {**out, "label": None if d["label"] == "Abstain" else d["label"], "abstained": d["label"] == "Abstain",
            "error": None, "explanation": d["explanation"], "evidence": d["evidence"]}


def b1(case: dict, cfg: ModelConfig) -> dict:
    res = chat(cfg, prompt("b1_system"), render_packet(case), ANSWER_SCHEMA)
    return _answer(res, [res])


def b1r(case: dict, cfg: ModelConfig) -> dict:
    first = chat(cfg, prompt("b1_system"), render_packet(case), ANSWER_SCHEMA)
    if not first.ok:
        return {**_answer(first, [first]), "first_label": None}
    import json as _json
    user = render_packet(case) + "\n\nProposed answer:\n" + _json.dumps(first.data, ensure_ascii=False)
    second = chat(cfg, prompt("b1r_review_system"), user, ANSWER_SCHEMA)
    return {**_answer(second, [first, second]), "first_label": first.data["label"]}


# ---------------------------------------------------------------- B2
REP = {"type": "object",
       "properties": {"requirement": {"type": "string"}, "decision": {"type": "string"},
                      "modality": {"type": "string", "enum": ["must", "must_not", "should", "should_not", "may",
                                                              "descriptive"]},
                      "condition": {"type": ["string", "null"]},
                      "condition_covers_task": {"type": "string", "enum": ["yes", "no", "no_condition", "unclear"]}},
       "required": ["requirement", "decision", "modality", "condition", "condition_covers_task"]}
EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {"instruction_1": REP, "instruction_2": REP,
                   "explicit_priority": {"type": "object",
                                         "properties": {"winner": {"type": "string", "enum": ["1", "2", "none"]},
                                                        "evidence": {"type": ["string", "null"]}},
                                         "required": ["winner", "evidence"]},
                   "evidence_sufficient": {"type": "boolean"}, "missing": {"type": ["string", "null"]}},
    "required": ["instruction_1", "instruction_2", "explicit_priority", "evidence_sufficient", "missing"],
}
COMPARE_SCHEMA = {
    "type": "object",
    "properties": {"same_decision": {"type": "boolean"},
                   "jointly_satisfiable": {"type": "string", "enum": ["yes", "no", "unclear"]},
                   "reason": {"type": "string"}},
    "required": ["same_decision", "jointly_satisfiable", "reason"],
}


def anchor(r: dict) -> str:
    return f"{r['path']}:{r['start_line']}" + (f"-{r['end_line']}" if r["end_line"] > r["start_line"] else "")


def b2(case: dict, cfg: ModelConfig) -> dict:
    pk = case["packet"]
    r = {1: pk["rule_1"], 2: pk["rule_2"]}
    target = case["target_path"]
    chain = loaded_set(target, pk["agents_paths"])
    trace: dict = {"loaded_set": chain}
    ex = chat(cfg, prompt("b2_extract_system"), render_packet(case), EXTRACT_SCHEMA)
    calls = [ex]
    if not ex.ok:
        return {**_answer(ex, calls), "trace": trace}
    e = ex.data
    trace["extraction"] = e
    evidence = [anchor(r[1]), anchor(r[2])]

    def done(label: str, why: str) -> dict:
        out = _answer(CallResult(True, {"label": label, "explanation": why, "evidence": evidence}, None, []), calls)
        out.update(calls=len(calls), input_tokens=sum(c.input_tokens for c in calls),
                   output_tokens=sum(c.output_tokens for c in calls),
                   latency_s=round(sum(c.latency_s for c in calls), 2),
                   retries=sum(len(c.attempts) - 1 for c in calls), attempts=[a for c in calls for a in c.attempts],
                   trace=trace)
        return out

    if not e["evidence_sufficient"]:
        return done("Insufficient evidence", f"Evidence insufficient: {e['missing'] or 'meaning not determinable'}.")
    inactive = []
    for n in (1, 2):
        if r[n]["path"] not in chain:
            inactive.append(f"Instruction {n} ({r[n]['path']}) is not on the ancestor chain of {target}")
        elif e[f"instruction_{n}"]["condition_covers_task"] == "no":
            inactive.append(f"Instruction {n}'s own condition ({e[f'instruction_{n}']['condition']}) excludes this "
                            "task")
    trace["inactive"] = inactive
    if inactive:
        return done("Disjoint applicability", "; ".join(inactive) + ".")
    if "descriptive" in (e["instruction_1"]["modality"], e["instruction_2"]["modality"]):
        return done("Compatible", "At least one instruction is descriptive and imposes no requirement, so both can "
                                  "be satisfied.")
    user = (f"Task: {case['task']}\nTarget file: {target}\n\n"
            f"Instruction 1 ({anchor(r[1])}): {r[1]['text']}\nRepresentation: {e['instruction_1']}\n\n"
            f"Instruction 2 ({anchor(r[2])}): {r[2]['text']}\nRepresentation: {e['instruction_2']}")
    cmp_ = chat(cfg, prompt("b2_compare_system"), user, COMPARE_SCHEMA)
    calls.append(cmp_)
    if not cmp_.ok:
        out = _answer(cmp_, calls)
        out["trace"] = trace
        return out
    c = cmp_.data
    trace["comparison"] = c
    if not c["same_decision"] or c["jointly_satisfiable"] == "yes":
        return done("Compatible", f"Both apply and can be satisfied together: {c['reason']}")
    if c["jointly_satisfiable"] == "unclear":
        return done("Insufficient evidence", f"Incompatibility could not be determined: {c['reason']}")
    winner = e["explicit_priority"]["winner"]
    if winner in ("1", "2"):
        if e["explicit_priority"]["evidence"]:
            evidence.append(e["explicit_priority"]["evidence"])
        return done("Valid override", f"Incompatible, and an explicit statement gives Instruction {winner} "
                                      f"precedence. {c['reason']}")
    sw = structural_winner(target, r[1]["path"], r[2]["path"])
    if sw:
        n = 1 if sw == "a" else 2
        return done("Valid override", f"Incompatible; Instruction {n} is in the more deeply nested file "
                                      f"{r[n]['path']} on the target's chain, so it takes precedence. {c['reason']}")
    return done("Unresolved conflict", f"Incompatible requirements with equal authority "
                                       f"({file_dir(r[1]['path']) or 'root'} vs {file_dir(r[2]['path']) or 'root'}) "
                                       f"and no explicit priority. {c['reason']}")
