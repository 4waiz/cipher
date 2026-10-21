# Submission handoff: EasyChair Submission 162 (TEXTUAL 2027)

Prepared 21 October 2026 (Asia/Dubai). Deadline: 23 October 2026 AoE = 24 October 2026, 15:59 UAE.

## File to upload

| Item | Value |
|---|---|
| PDF for Submission 162 | `C:\Users\awaiz\OneDrive\Desktop\CIPHER\submission\CIPHER_Submission_162.pdf` |
| SHA-256 | 5527745e14e4b2e53a7ef9f0a5000b01ea65215700840b13f3578513f8375858 (identical to the PDF on the website) |
| Category | Short / Vision Paper (TEXTUAL: "work-in-progress ... preliminary empirical results", up to 4 pages) |
| Pages | 4, including references (IEEEtran conference template, unmodified fonts and margins) |
| Manuscript version | 1.0.0, repository commit 0a4a71f |
| Anonymous fallback | `...\submission\CIPHER_Submission_162_anonymous_fallback.pdf` (only if the organisers require anonymity; no names, emails, or repository link in text, links, or metadata) |
| Revised abstract (optional) | `...\submission\Revised_abstract_for_EasyChair.md` (248 words) |

Upload with EasyChair "Update a File" for Submission 162. Do not create a new record. Nobody has uploaded anything yet.

## Requirements used

Official TEXTUAL 2027 page (accessed 21 Oct 2026): English, IEEE conference two-column format; Full (8 pages), Short/Vision
(4 pages), Tool & Dataset (4 pages); deadline 23 Oct 2026 AoE. Not stated anywhere: whether references count (the PDF is
4 pages including references), anonymity (named PDF used by default), preprint or artifact policy (the repository and
site are public because no rule restricts them). Details: `docs/venue_requirements.md`.

## Verified URLs (checked 21 Oct 2026)

| What | URL | Status |
|---|---|---|
| Repository (public) | https://github.com/4waiz/cipher | 200; CI green on 0a4a71f |
| Website | https://4waiz.github.io/cipher/ | 200 |
| Paper page | https://4waiz.github.io/cipher/paper/ | 200 |
| PDF | https://4waiz.github.io/cipher/paper/cipher-paper.pdf | 200, same SHA-256 as the upload file |
| Results / recorded cases | https://4waiz.github.io/cipher/results/ , https://4waiz.github.io/cipher/cases/ | 200; no horizontal scroll at 375 px |

## What was actually done

- Collected: 30 repositories retrieved at pinned commits from the Galster et al. dataset; 10 used (2 calibration, 8
  evaluation); 27 real instruction pairs, 27 constructed context variants, 27 order controls (81 evaluation cases).
- Human annotation: **none**. The blinded annotation packets and tool were built and released but not used (authors'
  decision on 21 Oct). No AI output is used as a reference label.
- Executed: B0 (keyword heuristic), B1 (direct model), B2 (structured pipeline), B1R (equal-call control) with
  Qwen3.6-35B-A3B locally; 81/81 cases per arm, no failures; sealed until the analysis was frozen.
- Measured: accuracy only on the 26 profile-determined cases; label-free measures elsewhere; one exploratory repeat check.

## Main findings (and negative results)

- B1, B2, and B1R were correct on all 26 profile-determined cases; B0 flagged 2 of them as conflicts.
- No model arm called any original or variant an unresolved conflict; all predictions were Compatible or Disjoint.
- The structured pipeline (B2) showed no measurable gain over the direct model and cost more (1.26 calls, 3,589 output
  tokens per case vs 1 and 2,177). The paper's hypothesis is not supported on the determined subset.
- Order swaps changed 4 of 27 predictions per arm, but an exact repeat of B1 changed 13 of 81 labels, so differences of
  a few cases are within run-to-run variation.
- Limitations: no human labels (RQ1 unanswered; semantic cases unscored), small challenge-oriented sample, one model and
  one profile, single run per arm.

## Reproduce

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv -e ".[dev]" pypandoc_binary==1.15
.venv/bin/python -m pytest
.venv/bin/python tools/check_provenance.py
.venv/bin/python analysis/corpus_stats.py
.venv/bin/python analysis/labelfree.py
.venv/bin/python analysis/exploratory.py
.venv/bin/python paper/build.py --tectonic /path/to/tectonic
.venv/bin/python site/build.py
```

## Before uploading, the authors must

1. All three authors read the whole PDF and agree to submit it. The Acknowledgment says "The authors reviewed the
   manuscript"; that must be true when you upload.
2. Confirm the AI-assistance acknowledgment (ChatGPT for the earlier proposal; Claude for software, experiments, reviews,
   and drafting) is accurate.
3. Decide whether to replace the EasyChair abstract. The registered abstract says annotators "will establish reference
   labels" and that the paper reports no results; the PDF now reports preliminary results without human labels. The
   revised text is in `Revised_abstract_for_EasyChair.md`.
4. Optional: send `docs/drafts/organizer_query.md` to textualw@gmail.com to confirm anonymity and the reference rule.
5. If you later collect human labels: regenerate the annotation keys with a secret salt and reissue packets (the issued
   packets carry the old scope-statement header), then run `analysis/results.py` (the human-label analysis).
