# CIPHER progress file

Resume point after any context reset. Update at every milestone.

Last updated: 2026-10-21 21:40 Asia/Dubai

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
| Human labels | **None; the authors decided not to annotate before the deadline (D18).** Paper reports a label-free + profile-determined analysis (addendum A2, Freeze 4) |
| Model | qwen3.6:35b-a3b via Ollama, digest a7eb95c5. gpt-oss:20b and gemma4 were removed from the machine during the session; do not rely on them |
| Dev runs | practice: all arms; calibration: B0, B1, B2 (dev1, schema defect found), B2 dev2 (fixed); B1R calibration stopped early (unchanged prompt) |
| Held-out runs | Primary v2 complete and sealed (B0, B1, B2, B1R: 81/81 each, 0 errors); `configs/heldout_runs.json` written. Secondary qwen3.5:9b B1/B2 running (optional; resumable with `sh runs/run_resume_v2.sh`). Sleep 17:29-19:19 and Ollama 0.40.6->0.40.7 auto-update logged in research_log.md |
| Paper | v1.0.0 compiles to 4 pages (named and anonymous), results from analysis/labelfree.py; final AI review pending |
| Site | Built by subagent; renders pending state; `python site/build.py` |
| GitHub | 4waiz/cipher private; CI and Pages workflows written (Pages needs a public repo or paid plan) |

## Next executable actions

1. Final independent AI review of paper vs evidence; fix concrete issues.
2. Make 4waiz/cipher public, enable Pages, verify live URLs.
3. Copy PDFs to Desktop\CIPHER\submission\, finish docs/HANDOFF.md.
