# CIPHER progress file

Resume point after any context reset. Update at every milestone.

Last updated: 2026-10-21 15:35 Asia/Dubai

## Hard dates

- Paper deadline: 23 Oct 2026 AoE = 24 Oct 2026 15:59 Asia/Dubai. Team upload target: 23 Oct (UAE).
- EasyChair Submission 162 (TEXTUAL track, saner27tracks). Do not create a new record. Do not click Submit for the author.

## State

| Item | Status |
|---|---|
| Venue rules | Verified: Short/Vision <= 4 pages, IEEE two-column. Anonymity, references-in-limit, preprint policy not stated (`docs/venue_requirements.md`) |
| Corpus | Frozen: 10 repos (2 calibration, 8 evaluation) at pinned commits; manifest sha256 4ff2cc31...f177 (`docs/freeze.md`) |
| Cases | Evaluation: 27 originals, 27 context variants, 27 order controls. Calibration: 7 + 7. Practice: 6 authored |
| Annotation packets | Issued 21 Oct to Desktop\CIPHER\annotation_packets (A1 Awaiz, A2 Mohammad); adjudicator Huda |
| Human labels | **None received yet** (`python -m cipher.reference status`) |
| Model | qwen3.6:35b-a3b via Ollama, digest a7eb95c5. gpt-oss:20b and gemma4 were removed from the machine during the session; do not rely on them |
| Dev runs | practice: all arms; calibration: B0, B1, B2 (dev1, schema defect found), B2 dev2 (fixed); B1R calibration stopped early (unchanged prompt) |
| Held-out runs | v1 superseded (stopped unopened after the review). Freeze 3 + 3b committed; v2 running since 15:13: B0 done, B1 in progress, then B2, B1R, secondary qwen3.5:9b (`runs/sealed/heldout_v2.log`, progress counts only). Slowed ~6x since 15:19 by the author's own `rabt-ai serve` process sharing the GPU |
| Paper | Draft compiles (3 pages without results); results prose goes in paper/prose/{abstract,headline,results,conclusion}.tex once labels are final |
| Site | Built by subagent; renders pending state; `python site/build.py` |
| GitHub | 4waiz/cipher private; CI and Pages workflows written (Pages needs a public repo or paid plan) |

## Next executable actions

1. Wait for the sealed runs (do not open predictions). `configs/heldout_runs.json` is written by runs/run_heldout.sh.
2. Wait for human files in annotations/submissions/ (calibration_A1/A2, evaluation_A1/A2).
3. When both evaluation submissions arrive: `python -m cipher.reference adjudication`; send Huda
   annotations/adjudication/CIPHER_adjudication_Huda.html, then CIPHER_transformation_review.html.
4. After Huda's two files: `python -m cipher.reference finalize`, `python -m cipher.unlock`, `python analysis/results.py`,
   write results prose in paper/body.tex (replace \ResultsSection, \AbstractText, \ConclusionText, \AIDisclosure,
   \ResultsHeadline), `python paper/build.py`, inspect pages, `python site/build.py`, AI review pass, handoff.
5. Contingency if labels are incomplete by 23 Oct UAE: no accuracy claims; tell the author exactly what is missing.
