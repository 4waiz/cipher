"""Candidate retrieval: which instruction pairs are shown to annotators and methods.

Retrieval is separate from classification. It is challenge-oriented: it prefers pairs that share a decision topic and
look as if they might disagree (different tool values, opposite polarity, conditions, precedence words). It therefore
cannot estimate how often conflicts occur, and any recall reported later is recall within this candidate set.
"""

from __future__ import annotations

import itertools
import random
import re
from dataclasses import dataclass

from .mdparse import Unit
from .profile import relation

DIRECTIVE = re.compile(
    r"^(?:\*\*[^*]+\*\*:?\s*)?(use|run|do|don't|never|always|prefer|avoid|keep|add|write|follow|ensure|make|put|place|"
    r"create|update|check|test|format|commit|install|include|import|name|document|mark|place|start|read|call|return|"
    r"store|set|pin|wrap|log|handle|raise|throw|limit|stick|favor|favour|treat|leave|remove|delete|regenerate|edit|"
    r"modify|change|open|push|squash|rebase|lint|build|validate|verify|reference|annotate|declare|export)\b"
    r"|\b(must|should|shall|never|always|do not|don't|prefer|avoid|mandatory|forbidden|not allowed)\b",
    re.I,
)

TOPICS: dict[str, re.Pattern] = {
    "formatting": re.compile(r"\b(indent\w*|tabs?|spaces?|formatt\w*|prettier|black|ruff format|gofmt|rustfmt|"
                             r"clang-format|line length|line-length|max line|trailing|quotes?|semicolons?)\b", re.I),
    "testing": re.compile(r"\b(tests?|testing|pytest|jest|vitest|mocha|unittest|cargo test|go test|coverage|spec|"
                          r"e2e|playwright|junit|snapshot)\b", re.I),
    "package_management": re.compile(r"\b(npm|pnpm|yarn|bun|pip|uv|poetry|conda|pixi|cargo add|go get|gradle|maven|"
                                     r"mvn|dependenc\w*|lockfile|package\.json|pyproject)\b", re.I),
    "linting_typing": re.compile(r"\b(lint\w*|eslint|ruff|clippy|mypy|pyright|tsc|type[- ]?check\w*|typing|types?|"
                                 r"any\b|strict)\b", re.I),
    "build_commands": re.compile(r"\b(make|build|compile|cmake|bazel|just|task|script|command)\b", re.I),
    "vcs": re.compile(r"\b(commit\w*|pull request|PRs?|branch\w*|changelog|rebase|squash|push|merge)\b", re.I),
    "docs": re.compile(r"\b(docs?|documentation|docstrings?|README|comments?|jsdoc|markdown)\b", re.I),
    "logging_errors": re.compile(r"\b(log\w*|console\.log|print\w*|errors?|exceptions?|panic|unwrap|raise|throw)\b",
                                 re.I),
    "naming_style": re.compile(r"\b(naming|names?|camelCase|snake_case|PascalCase|kebab|style|convention\w*)\b", re.I),
    "imports_modules": re.compile(r"\b(imports?|exports?|modules?|ESM|CommonJS|require)\b", re.I),
    "generated_code": re.compile(r"\b(generated|codegen|regenerat\w*|do not edit|auto-?generated|golden)\b", re.I),
}

ALTERNATIVES = [
    ["npm", "pnpm", "yarn", "bun"], ["pip", "uv", "poetry", "conda", "pixi"], ["jest", "vitest", "mocha", "pytest",
    "unittest", "playwright"], ["tabs", "spaces"], ["2 spaces", "4 spaces", "two spaces", "four spaces"],
    ["prettier", "biome", "eslint", "black", "ruff"], ["gradle", "maven", "mvn"], ["pixi", "bazel", "cmake"],
    ["esm", "commonjs"], ["camelcase", "snake_case", "pascalcase", "kebab-case"],
]
NEGATION = re.compile(r"\b(never|don't|do not|avoid|must not|mustn't|should not|shouldn't|no longer|not allowed|"
                      r"forbidden|don’t)\b", re.I)
CONDITION = re.compile(r"\b(when|if|unless|except|only|for (?:all |any )?\w+ (?:files|code|changes|tests)|"
                       r"in this (?:directory|folder|package|module|crate))\b", re.I)
PRECEDENCE = re.compile(r"\b(overrid\w*|precedence|supersed\w*|take[s]? priority|instead of|rather than|regardless)\b",
                        re.I)


def is_candidate_unit(u: Unit) -> bool:
    if u.kind == "table_row":
        return False
    t = u.text
    if not (25 <= len(t) <= 400):
        return False
    if re.fullmatch(r"[`\[\]()\w./:#-]+(?:\s*[—-]\s*.*)?", t) and not DIRECTIVE.search(t):
        return False
    return bool(DIRECTIVE.search(t))


def topics(t: str) -> set[str]:
    return {name for name, rx in TOPICS.items() if rx.search(t)}


def alt_values(t: str) -> list[set[str]]:
    low = t.lower()
    return [{v for v in fam if re.search(r"(?<![\w-])" + re.escape(v) + r"(?![\w-])", low)} for fam in ALTERNATIVES]


@dataclass
class Candidate:
    a: Unit
    b: Unit
    relation: str
    shared_topics: list[str]
    score: int
    signals: list[str]


SALIENT = re.compile(
    r"(npm|pnpm|yarn|bun|pip|uv|poetry|conda|pixi|cargo|go test|gofmt|rustfmt|clippy|pytest|jest|vitest|mocha|"
    r"playwright|cypress|unittest|ruff|eslint|prettier|biome|black|isort|mypy|pyright|tsc|gradle|maven|mvn|"
    r"bazel|cmake|docker|tabs?|spaces?|indent\w*|line length|console\.log|println!?|logger|logging|"
    r"tracing|assert\w*|mocks?|snapshots?|fixtures?|golden|changelog|signed-off-by|conventional "
    r"commits?|docstrings?|jsdoc|README|migrations?|lockfile|uv\.lock|package\.json|pyproject\.toml|"
    r"type hints?|camelCase|snake_case|PascalCase|ESM|CommonJS|codegen|"
    r"pre-commit|lint\w*|format\w*|coverage|e2e|integration tests?|unit tests?|tests?)",
    re.I,
)


def norm(t: str) -> str:
    return re.sub(r"\W+", " ", t).strip().lower()


def salient(t: str) -> set[str]:
    terms = {m.group(1).lower().rstrip("s").rstrip("(") for m in SALIENT.finditer(t)}
    for code in re.findall(r"`([^`]+)`", t):
        head = code.strip().split()[0].lower() if code.strip() else ""
        if re.fullmatch(r"[a-z][\w.-]{1,30}", head):
            terms.add("`" + head)
    return terms


def score_pair(a: Unit, b: Unit) -> Candidate | None:
    """Score a pair as an apparent-conflict candidate. A pair qualifies only if it shares a specific term (tool,
    command head, or convention word) or names different values from one alternative family."""
    rel = relation(a.path, b.path)
    if norm(a.text) == norm(b.text):
        return None  # verbatim duplicates are a duplication smell, not an apparent disagreement
    shared_terms = sorted(salient(a.text) & salient(b.text))
    different = any(va and vb and va != vb for va, vb in zip(alt_values(a.text), alt_values(b.text)))
    if not shared_terms and not different:
        return None
    signals = []
    score = 2 if shared_terms else 0
    if different:
        score += 3
        signals.append("different_values")
    if shared_terms and bool(NEGATION.search(a.text)) != bool(NEGATION.search(b.text)):
        score += 1
        signals.append("opposite_polarity")
    if CONDITION.search(a.text) or CONDITION.search(b.text):
        score += 1
        signals.append("condition_marker")
    if PRECEDENCE.search(a.text) or PRECEDENCE.search(b.text):
        score += 1
        signals.append("precedence_marker")
    if rel == "same_file" and not ({"condition_marker", "precedence_marker", "different_values"} & set(signals)):
        return None
    shared_topics = sorted(topics(a.text) & topics(b.text))
    return Candidate(a, b, rel, shared_topics or shared_terms[:2], score, signals + [f"shared:{','.join(shared_terms[:4])}"])


def inventory(units_by_file: dict[str, list[Unit]]) -> list[Candidate]:
    """All scored candidate pairs in one repository snapshot (pairs within or across files)."""
    pool = [u for us in units_by_file.values() for u in us if is_candidate_unit(u)]
    out = []
    for a, b in itertools.combinations(pool, 2):
        c = score_pair(a, b)
        if c is not None:
            out.append(c)
    return out


QUOTA = ["ancestor_descendant", "ancestor_descendant", "unrelated", "any"]


def select(cands: list[Candidate], k: int, rng: random.Random) -> list[Candidate]:
    """Pick k pairs: two ancestor-descendant, one unrelated-branch, one of any relation (falling back when a
    relation is unavailable). Highest score first, seeded random tie-break; each unit is used at most once and each
    file pair at most twice."""
    order = sorted(cands, key=lambda c: (-c.score, rng.random()))
    chosen: list[Candidate] = []
    used_units: set[tuple[str, int]] = set()
    file_pairs: dict[tuple[str, str], int] = {}

    def ok(c: Candidate) -> bool:
        ka, kb = (c.a.path, c.a.start_line), (c.b.path, c.b.start_line)
        fp = tuple(sorted((c.a.path, c.b.path)))
        return ka not in used_units and kb not in used_units and file_pairs.get(fp, 0) < 2

    def take(c: Candidate) -> None:
        chosen.append(c)
        used_units.update({(c.a.path, c.a.start_line), (c.b.path, c.b.start_line)})
        fp = tuple(sorted((c.a.path, c.b.path)))
        file_pairs[fp] = file_pairs.get(fp, 0) + 1

    for want in (QUOTA * ((k + len(QUOTA) - 1) // len(QUOTA)))[:k]:
        pick = next((c for c in order if ok(c) and (want == "any" or c.relation == want)), None)
        if pick is None:
            pick = next((c for c in order if ok(c)), None)
        if pick is None:
            break
        take(pick)
    return chosen
