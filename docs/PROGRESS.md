# CIPHER progress file

Resume point after any context reset. Update at every milestone.

Last updated: 2026-10-21 (afternoon, Asia/Dubai)

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
| Dev runs | practice: B0/B1/B2/B1R done; calibration: running (`runs/dev/calibration_run.log`) |
| Held-out runs | Not started. Must be sealed in runs/sealed/ and run one arm at a time |
| Paper | Draft compiles (3 pages without results). Results macros pending |
| Site | Built by subagent; renders pending state; `python site/build.py` |
| GitHub | 4waiz/cipher private; CI and Pages workflows written (Pages needs a public repo or paid plan) |

## Next executable actions

1. When calibration runs finish: inspect only for systematic failures (format, profile misreading); freeze methods
   (Freeze 2 in docs/freeze.md); write `configs/heldout_runs.json`.
2. Run held-out arms sequentially: `sh runs/run_heldout.sh` (B0, B1, B2, B1R), sealed.
3. When both evaluation submissions arrive: `python -m cipher.reference adjudication` -> send Huda the adjudication
   packet and the transformation review sheet; then `finalize`, unlock runs, `python analysis/results.py`, write
   results prose, `python paper/build.py`, render-check pages, `python site/build.py`.
