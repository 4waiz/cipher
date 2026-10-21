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

## Secondary analysis (declared before any held-out prediction existed; run only if GPU time permits)

B1 and B2 repeated with the smaller local model `qwen3.5:9b` (Ollama digest recorded in its run manifest), same
prompts, schemas, decoding settings and evidence. Purpose: whether the structured pipeline's effect differs for a
smaller model. Reported in the artifact; in the paper at most as one sentence, labelled secondary.

## Addendum A1 (2026-10-21, before any held-out prediction was inspected; prompted by an independent code review)

1. Context variants are scored only after the human transformation check marks them valid; without the check they stay
   pending (previously the rule applied only when a review file existed). Order controls are unchanged (they also
   require the check).
2. Evidence-anchor validity counts only model-produced anchors: B1 and B1R anchors, and B2's optional explicit-priority
   anchor (B2's two span anchors are written by code). A range `path:a-b` is valid only if the whole range lies inside
   a section shown to the model, or `a = b` is a listed scope line.
3. The execution table reports, per method: cases, labelled cases (coverage), failures (including missing
   predictions), abstentions, malformed or schema-violating attempts, truncated attempts, API errors, retries, calls,
   mean input and output tokens, mean latency.
4. Illustrative cases follow the declared rule and are exported in `metrics.json` (`illustrative`).
5. No human semantic-support audit of explanations was performed; this is stated rather than reported.
6. The primary held-out runs are the v2 runs (Freeze 3). The v1 runs were stopped before inspection and are not analysed.
7. The secondary qwen3.5:9b runs are analysed on originals only (correct count and macro-F1), labelled secondary.
8. Analysis code hashes are recorded in `docs/freeze.md` (Freeze 3b) and in `runs/heldout/UNLOCK.json`.

## Addendum A2 (2026-10-21 21:15, before any held-out prediction was inspected): analysis without human labels

On 21 October at about 21:05 the corresponding author reported that the human annotation will not be carried out for
this submission. No AI output may stand in for human labels, so the primary analysis above (which needs human reference
labels) cannot be run. The following label-free and profile-determined analysis replaces it for this submission; the
human-labelled evaluation remains future work. No outcome below was chosen after seeing predictions.

**Profile-determined reference (PD).** A case is profile-determined when the AGENTS.md file of at least one of its two
instructions is not on the target's directory chain (`cipher.profile.loaded_set`). Under P1 that instruction is not
loaded, so the decision sequence ends at step 2 and the label is *Disjoint applicability*. PD is computed from file
paths only. It covers 26 evaluation cases (5 originals, 16 target-path variants, 5 order controls). B2 computes the
loaded set in code, so its PD accuracy measures what explicit structure guarantees, not semantic reasoning; this is
stated wherever PD results appear.

**Primary outcome (A2).** Correct-label count on the 21 PD originals and variants (order controls excluded), B2 versus
B1, with discordant pairs (B2 right and B1 wrong; B1 right and B2 wrong). Abstentions and failures are incorrect.

**Secondary outcomes (A2).**
1. PD cases, every method: predicted-label breakdown; B0 and model false-conflict count (predictions of "Unresolved
   conflict" or B0 flags on PD cases, all of which are reference Disjoint).
2. All 81 cases, label-free: predicted-label distribution per method and stratum; share of cases each method calls an
   unresolved conflict; B0 flag count.
3. Agreement between methods (B1, B2, B1R): exact agreement and Cohen's kappa on originals and on variants. This is
   agreement between systems, not accuracy.
4. Order-control stability: identical prediction for original and control (27 pairs per method); on the 5 PD pairs,
   both correct.
5. Context sensitivity: for the 16 target-path variants, variant correct (PD) and prediction changed from its original;
   for the 11 placement variants, prediction changed (label-free).
6. B1R: how often self-review changed B1-style first answers.
7. Execution: calls, tokens, failures, retries, abstentions; latency reported but not compared (GPU shared with another
   process 15:19-16:20 and an Ollama patch update during the runs).
8. Illustrative cases by rule: the first PD case (by ID) that B1 gets wrong, and the first non-PD original (by ID)
   where B1 and B2 disagree, shown without asserting which is right.

Not reported: accuracy or macro-F1 on non-PD cases, human agreement (RQ1), anything requiring human labels. The secondary
qwen3.5:9b analysis was stopped incomplete (16/81 B1 cases) and is not reported.
