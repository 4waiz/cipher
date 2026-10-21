# Analysis plan (frozen before any held-out prediction is inspected)

Version 1.0, 2026-10-21. The commit that adds this file, together with its SHA-256 in `docs/freeze.md`, records the
freeze. This is an internal freeze, not an external preregistration.

## Units, strata, reference labels

- Unit: one case = two instruction spans + one task + one target path + one pinned commit + profile P1.
- Strata (reported separately, never pooled for the primary outcome): `original`, `context_variant`, `order_control`.
- Reference labels: two independent annotators (A1, A2) label every evaluation original and context variant. Agreed
  labels become reference labels; disagreements are adjudicated by a third author who sees both judgments. Initial
  judgments are preserved.
- An order control inherits its parent's reference label only after a human check confirms that the control differs
  from its parent only in the order of the two instructions. Unverified controls are excluded and counted.
- Cases whose final reference label is missing are excluded from scoring and counted.

## Primary outcome

Five-class macro-F1 on evaluation `original` cases, B2 versus B1, same cases, same model.
- Macro average over the classes with non-zero reference support in that stratum; absent classes are listed.
- A prediction that is an abstention or a system failure (no valid label after retries) is counted as incorrect: it
  matches no class, lowers recall of the reference class, and adds no false positive to any class.
- The paired difference is reported with per-repository counts and a repository-cluster bootstrap 95% percentile
  interval (2,000 resamples of the 8 repositories, seed 20261021). With 8 clusters the interval is descriptive only; no
  significance test is the basis of a claim.

## Secondary outcomes (all methods unless stated)

1. Five-class accuracy and the confusion matrix per stratum, with class supports.
2. Per-class precision, recall, F1 with counts.
3. Binary conflict detection (positive = reference "Unresolved conflict"; predicted positive = label "Unresolved
   conflict", or B0 flag = true): precision, recall, F1 with numerators and denominators. An empty denominator is
   reported as undefined. Abstentions and failures on reference conflicts count as misses; on negatives they are not
   false alarms. B0 is scored only on these binary metrics.
4. False-conflict rate on reference "Valid override" cases and on reference "Disjoint applicability" cases: share
   predicted "Unresolved conflict" (or B0 flag), with denominators.
5. Context variants: both-correct rate over (original, variant) pairs with both references available; reported overall
   and for pairs whose reference label changed versus stayed the same.
6. Order controls: correct-and-stable rate (original and control both correct) and raw stability (same prediction,
   right or wrong). Identical wrong predictions count as stable but not correct.
7. Human agreement before adjudication: raw agreement and Cohen's kappa on evaluation originals and on variants,
   with the annotator-by-annotator contingency table and per-class counts.
8. Evidence anchors: share of cited `path:line` anchors that point to a file shown in the packet and a line inside the
   shown span or section. A separate semantic-support audit of explanations is reported only if a human performs it;
   otherwise its absence is stated.
9. Execution: coverage, abstentions, malformed or schema-violating outputs, API failures, retries, calls, input and
   output tokens, latency per method.

## Arms and budgets

B0 (heuristic, no model calls), B1 (1 call per case), B2 (1-2 calls per case), B1R (2 calls per case; equal-call
control for B2). One run per arm with fixed decoding settings and seed; no repetitions. B1R is secondary.

## Rules

- No prompt, schema, parser, mapping, or selection change after held-out predictions are inspected. If one is made, the
  original run is preserved and the new analysis is labelled exploratory.
- Calibration cases are never scored as held-out data.
- Illustrative cases in the paper are chosen by rule: the first case (by case ID) in each of these groups, where it
  exists: B2 correct and B1 wrong; B1 correct and B2 wrong; both wrong.
