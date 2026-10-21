# CIPHER protocol and data card

## Purpose

Test whether making applicability (which AGENTS.md files and conditions apply to a task's target) and precedence
(nested files over ancestors) explicit improves the classification of apparent instruction conflicts. RQ1: how reliably
do two independent annotators distinguish the five labels? RQ2: does the structured pipeline (B2) beat a direct model
with the same evidence (B1)? RQ3: do predictions change correctly under relevant context changes and stay correct under
order changes?

## Composition

| Split | Repositories | Originals | Context variants | Order controls | Practice |
|---|---|---|---|---|---|
| Practice (authored, never scored) | 1 invented example | | | | 6 |
| Calibration | 2 | 7 | 7 | 0 | |
| Evaluation | 8 | 27 | 27 | 27 | |

A case = two verbatim instruction spans (path, lines, heading, enclosing section), one task editing one target file,
one pinned commit, profile P1. Fields: see `data/cases/manifest.json`. Original = genuine text and placement with a
researcher-authored task. Context variant = one documented property changed (target path, or placement of one
instruction); wording unchanged. Order control = presentation order of the two instructions swapped.

## Collection

1. Discovery frame: `context_files.csv` (Galster et al., Zenodo 20090356, SHA-256 e5dd3043...840fc). 237 repositories
   whose rows show a root AGENTS.md and at least one eligible nested AGENTS.md (pointer files excluded; nested files in
   hidden, template, example, vendored, fixture or test-data directories excluded as separate project roots).
2. Seeded order (seed 20261021); the first 30 retrieved through the GitHub API at the default-branch HEAD on
   2026-10-21 (`data/acquisition_log.json`). Every AGENTS.md stored with Git blob SHA and SHA-256.
3. Snapshot eligibility: open-source licence detected by GitHub; not fork or archived; tree not truncated; no
   symlinked AGENTS.md; root and at least one nested file with five or more non-empty lines (24 of 30).
4. Candidate pairs (`src/cipher/candidates.py`): directive units outside code fences; pairs sharing a specific term
   or naming different values of one family; verbatim duplicates excluded; challenge-oriented score. Repository
   eligibility: at least 4 pairs, at least 2 across files (12 of 24). First 2 in frame order -> calibration, next 8 ->
   evaluation; others unused. Up to 4 pairs per repository by score with relation quotas.
5. Targets: real files under the relevant directory (seeded choice among the shallowest code or documentation files);
   tasks from fixed templates.

## Annotation

Handbook v1.0 (`docs/annotation_handbook.md`), standalone HTML packets with per-annotator seeds and opaque IDs.
Hidden from annotators: predictions, strata, transformations, families, the other annotator's answers. Calibration
round (20 items incl. 6 authored practice items with feedback) precedes evaluation (54 items). Disagreements go to an
adjudicator who sees both judgments (anonymised as X/Y). Initial judgments are preserved. Order controls inherit the
parent's final label after a human transformation check. Agreement: raw and Cohen's kappa before adjudication.

## Methods and runs

B0, B1, B2, B1R as described in `src/cipher/methods.py`; prompts in `configs/prompts/`; decoding and retries in
`src/cipher/llm.py`. Held-out runs are sealed until labels are final; analysis follows `docs/analysis_plan.md`.

## Intended use and limits

For studying the classification of apparent instruction conflicts under one declared profile. Not a prevalence
estimate, not a measure of agent behaviour, and not a judgement of any repository's quality. Mined text is research data
only; it was never executed or followed.

## Distribution and maintenance

Public GitHub repository `4waiz/cipher` (MIT code; third-party text under its own licences, `DATA_LICENSE.md`).
Contact: the corresponding author, Awaiz Ahmed.
