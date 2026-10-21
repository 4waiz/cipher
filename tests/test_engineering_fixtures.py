"""Engineering fixtures: hand-made inputs that test invariants of the code. They are not research data, and their
results are never written to the research-result directories."""

import json

from cipher import metrics as M
from cipher.llm import validate
from cipher.mdparse import section_text, units
from cipher.methods import ANSWER_SCHEMA, b0, b2
from cipher.practice import practice_items
from cipher.profile import loaded_set, relation, structural_winner

AGENTS = ["AGENTS.md", "web/AGENTS.md", "api/AGENTS.md", "web/src/AGENTS.md"]


def test_path_ancestry_and_loaded_set():
    assert loaded_set("web/src/button.ts", AGENTS) == ["AGENTS.md", "web/AGENTS.md", "web/src/AGENTS.md"]
    assert loaded_set("api/x.py", AGENTS) == ["AGENTS.md", "api/AGENTS.md"]
    assert loaded_set("README.md", AGENTS) == ["AGENTS.md"]
    assert loaded_set("webapp/x.ts", AGENTS) == ["AGENTS.md"]  # prefix of a directory name is not an ancestor


def test_relation_and_structural_winner():
    assert relation("AGENTS.md", "AGENTS.md") == "same_file"
    assert relation("AGENTS.md", "web/AGENTS.md") == "ancestor_descendant"
    assert relation("web/AGENTS.md", "api/AGENTS.md") == "unrelated"
    assert structural_winner("web/src/b.ts", "AGENTS.md", "web/AGENTS.md") == "b"
    assert structural_winner("web/src/b.ts", "AGENTS.md", "AGENTS.md") is None  # equal authority
    assert structural_winner("web/src/b.ts", "AGENTS.md", "api/AGENTS.md") is None  # api not loaded


def test_markdown_units_spans_and_fences():
    text = "# T\n\n## Style\n- Use four spaces.\n  continued line\n\n```\n- not a rule\n```\n- Prefer x.\n"
    us = units("AGENTS.md", text)
    assert [(u.start_line, u.end_line, u.text) for u in us] == [
        (4, 5, "Use four spaces. continued line"), (10, 10, "Prefer x.")]
    assert us[0].heading_path == ["T", "Style"]
    first, last, sec = section_text(text, 4, 5)
    assert first == 3 and sec.startswith("## Style")


def _with_extraction(case, ext, cmp_=None):
    """Run B2 with a fake model that returns fixed structured outputs (no network)."""
    import cipher.methods as mm
    from cipher.llm import CallResult
    calls = iter([ext] + ([cmp_] if cmp_ else []))

    def fake_chat(cfg, system, user, schema):
        d = next(calls)
        assert validate(d, schema) is None
        return CallResult(True, d, None, [{"status": "ok", "input_tokens": 10, "output_tokens": 5, "latency_s": 0.1}])
    orig = mm.chat
    mm.chat = fake_chat
    try:
        return b2(case, None)
    finally:
        mm.chat = orig


REP = {"requirement": "r", "decision": "indentation width", "modality": "must", "condition": None,
       "condition_covers_task": "no_condition"}
EXT = {"instruction_1": REP, "instruction_2": REP, "explicit_priority": {"winner": "none", "evidence": None},
       "evidence_sufficient": True, "missing": None}
INCOMPAT = {"same_decision": True, "jointly_satisfiable": "no", "reason": "4 vs 2 spaces"}


def test_b2_resolution_rules_on_authored_items():
    p = {c["case_id"]: c for c in practice_items()}
    assert _with_extraction(p["P1"], EXT, INCOMPAT)["label"] == "Unresolved conflict"  # equal authority
    assert _with_extraction(p["P2"], EXT, INCOMPAT)["label"] == "Valid override"  # deeper file wins
    out = _with_extraction(p["P3"], EXT)  # api/AGENTS.md not loaded: no comparison call is made
    assert out["label"] == "Disjoint applicability" and out["calls"] == 1
    cond = dict(EXT, instruction_1=dict(REP, condition="Python code", condition_covers_task="no"))
    assert _with_extraction(p["P5"], cond)["label"] == "Disjoint applicability"
    compat = {"same_decision": False, "jointly_satisfiable": "yes", "reason": "different decisions"}
    assert _with_extraction(p["P4"], EXT, compat)["label"] == "Compatible"
    assert _with_extraction(p["P6"], dict(EXT, evidence_sufficient=False, missing="usual conventions"))["label"] \
        == "Insufficient evidence"
    explicit = dict(EXT, explicit_priority={"winner": "1", "evidence": "AGENTS.md:3"})
    assert _with_extraction(p["P1"], explicit, INCOMPAT)["label"] == "Valid override"


def test_malformed_outputs_are_rejected():
    assert validate({"label": "Compatible", "explanation": "x", "evidence": []}, ANSWER_SCHEMA) is None
    assert validate({"label": "Conflict", "explanation": "x", "evidence": []}, ANSWER_SCHEMA)
    assert validate({"label": "Compatible", "evidence": []}, ANSWER_SCHEMA)
    assert validate({"label": "Compatible", "explanation": "x", "evidence": [3]}, ANSWER_SCHEMA)


def test_b0_ruleherd_adaptation():
    p = {c["case_id"]: c for c in practice_items()}
    assert b0(p["P1"])["conflict_flag"] is False  # same file is never compared, as in Ruleherd
    assert b0(p["P2"])["conflict_flag"] is False  # 4 vs 2 spaces is outside Ruleherd's tabs/spaces lexicon
    case = json.loads(json.dumps(p["P2"]))
    case["packet"]["rule_1"]["text"] = "- Always use npm install for dependencies."
    case["packet"]["rule_2"]["text"] = "- Use pnpm install for dependencies."
    assert b0(case)["conflict_flag"] is True
    case["packet"]["rule_2"]["text"] = "- Never use pnpm install."
    assert b0(case)["conflict_flag"] is False  # negated clauses carry no stance


def test_scoring_edge_cases():
    gold = ["Compatible", "Compatible", "Disjoint applicability"]
    assert M.binary_conflict(gold, [False, False, False])["precision"] is None  # no flags: undefined, not perfect
    assert M.binary_conflict(gold, [False, False, False])["recall"] is None  # no positives: undefined
    pred = ["Compatible", None, "Disjoint applicability"]  # None = abstention or failure
    assert M.accuracy(gold, pred) == 2 / 3
    score, absent = M.macro_f1(gold, pred)
    assert set(absent) == {"Unresolved conflict", "Valid override", "Insufficient evidence"}
    assert abs(score - (2 / 3 + 1.0) / 2) < 1e-9
    assert M.binary_conflict(["Unresolved conflict"], [None])["recall"] == 0.0  # abstention misses a conflict
    assert M.binary_conflict(["Compatible"], [None])["fp"] == 0  # and is not a false alarm
    bc = M.both_correct([("Compatible", "Compatible", "Compatible", "Compatible"),
                         ("Valid override", "Compatible", "Valid override", "Compatible")])
    assert bc["both_correct"] == 1 and bc["same_prediction"] == 2  # identical wrong answers are not a pass
    assert M.cohen_kappa(["a", "b"], ["a", "b"])["kappa"] == 1.0


def test_cluster_bootstrap_is_deterministic():
    rows = [{"repo": r, "x": v} for r, v in [("a", 1), ("a", 0), ("b", 1), ("c", 1)]]
    stat = lambda s: sum(r["x"] for r in s) / len(s)  # noqa: E731
    assert M.cluster_bootstrap(rows, stat, reps=200) == M.cluster_bootstrap(rows, stat, reps=200)
