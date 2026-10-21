"""Scoring functions. Pure, deterministic, and tested with engineering fixtures in tests/."""

from __future__ import annotations

import random
from collections import Counter

LABELS = ["Unresolved conflict", "Valid override", "Disjoint applicability", "Compatible", "Insufficient evidence"]
CONFLICT = "Unresolved conflict"


def safe_div(n: float, d: float) -> float | None:
    return None if d == 0 else n / d


def confusion(gold: list[str], pred: list[str | None]) -> dict[str, dict[str, int]]:
    """Rows = reference label, columns = predicted label plus 'none' (abstention or failure)."""
    cols = LABELS + ["none"]
    m = {g: {c: 0 for c in cols} for g in LABELS}
    for g, p in zip(gold, pred):
        m[g][p if p in LABELS else "none"] += 1
    return m


def per_class(gold: list[str], pred: list[str | None]) -> dict[str, dict]:
    out = {}
    for c in LABELS:
        tp = sum(1 for g, p in zip(gold, pred) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred) if g == c and p != c)
        prec, rec = safe_div(tp, tp + fp), safe_div(tp, tp + fn)
        f1 = None if prec is None or rec is None else (0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
        if rec is not None and prec is None:
            f1 = 0.0  # class present in the reference, never predicted
        out[c] = {"support": tp + fn, "predicted": tp + fp, "tp": tp, "precision": prec, "recall": rec, "f1": f1}
    return out


def macro_f1(gold: list[str], pred: list[str | None]) -> tuple[float | None, list[str]]:
    """Macro-F1 over classes with non-zero reference support. Returns (score, absent classes)."""
    pc = per_class(gold, pred)
    present = [c for c in LABELS if pc[c]["support"] > 0]
    absent = [c for c in LABELS if pc[c]["support"] == 0]
    if not present:
        return None, absent
    return sum(pc[c]["f1"] for c in present) / len(present), absent


def accuracy(gold: list[str], pred: list[str | None]) -> float | None:
    return safe_div(sum(1 for g, p in zip(gold, pred) if g == p), len(gold))


def binary_conflict(gold: list[str], flags: list[bool | None]) -> dict:
    """flags: True = conflict predicted, False = not, None = abstention/failure (a miss on positives, not an alarm)."""
    tp = sum(1 for g, f in zip(gold, flags) if g == CONFLICT and f is True)
    fp = sum(1 for g, f in zip(gold, flags) if g != CONFLICT and f is True)
    pos = sum(1 for g in gold if g == CONFLICT)
    flagged = tp + fp
    prec, rec = safe_div(tp, flagged), safe_div(tp, pos)
    f1 = None if prec is None or rec is None else (0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))
    return {"tp": tp, "fp": fp, "flagged": flagged, "positives": pos, "precision": prec, "recall": rec, "f1": f1}


def false_conflict_rate(gold: list[str], flags: list[bool | None], cls: str) -> dict:
    n = sum(1 for g in gold if g == cls)
    k = sum(1 for g, f in zip(gold, flags) if g == cls and f is True)
    return {"class": cls, "false_conflicts": k, "n": n, "rate": safe_div(k, n)}


def both_correct(pairs: list[tuple[str, str | None, str, str | None]]) -> dict:
    """pairs: (gold_a, pred_a, gold_b, pred_b). Both-correct requires each prediction to equal its own reference."""
    n = len(pairs)
    k = sum(1 for ga, pa, gb, pb in pairs if pa == ga and pb == gb)
    stable = sum(1 for ga, pa, gb, pb in pairs if pa is not None and pa == pb)
    return {"n": n, "both_correct": k, "rate": safe_div(k, n), "same_prediction": stable}


def cohen_kappa(a: list[str], b: list[str]) -> dict:
    n = len(a)
    if n == 0:
        return {"n": 0, "observed": None, "expected": None, "kappa": None}
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    kappa = None if pe == 1 else (po - pe) / (1 - pe)
    return {"n": n, "observed": po, "expected": pe, "kappa": kappa}


def cluster_bootstrap(rows: list[dict], stat, clusters_key: str = "repo", reps: int = 2000,
                      seed: int = 20261021) -> dict:
    """Percentile interval from resampling whole clusters (repositories) with replacement."""
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r[clusters_key], []).append(r)
    keys = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = [r for k in (rng.choice(keys) for _ in keys) for r in by[k]]
        v = stat(sample)
        if v is not None:
            vals.append(v)
    vals.sort()
    if not vals:
        return {"lo": None, "hi": None, "reps": 0}
    return {"lo": vals[int(0.025 * len(vals))], "hi": vals[min(len(vals) - 1, int(0.975 * len(vals)))],
            "reps": len(vals), "clusters": len(keys)}
