# Research log

Chronological record of what was done and observed. Times are Asia/Dubai.

## 2026-10-21

- 13:03 Inventory of supplied package: `CIPHER_Paper.pdf` (3 pages, IEEEtran, proposal), `CIPHER_Anonymous.pdf` (3 pages),
  `CIPHER_Manuscript.docx`, `CIPHER_Research_and_Submission_Guide.docx`, `source/` with two .tex files, abstract,
  reading list, proposed annotation template. No code, dataset, annotations, model outputs, or results existed.
- 13:05 Environment: Windows 11, Python 3.12.10, uv 0.11.19, Node 24.16, git 2.54, gh 2.95 (authenticated as 4waiz,
  scopes repo/workflow), Ollama 0.40.6 with qwen3.6:35b-a3b, gemma4:26b-a4b-it-qat, gpt-oss:20b, qwen3.5:9b and smaller
  models. GPU: RTX 5080 Laptop, 16 GB. No LaTeX, no pandoc. No model API key in the environment.
- 13:07 TEXTUAL official page retrieved; requirements recorded in `venue_requirements.md`.
- 13:08 Galster et al. dataset located (moved to https://se-uhd.de/agentcontext-dataset/); Zenodo record 20090356.
  `context_files.csv`: 9,470 rows; 3,703 AGENTS.md rows in 2,136 repositories; 434 repositories have a nested AGENTS.md
  row; 321 have two or more AGENTS.md rows.
- 13:09 Tectonic 0.17.0 compiled the archived proposal source successfully.
- 13:12 Ruleherd inspected at commit 94559fc6399a5fbf77c2f76f96172d2207d32e8d (package version 0.1.3, MIT).
- 13:20-13:45 Corpus frozen (manifest 4ff2cc31...f177 after LF normalisation); annotation packets issued to
  `Desktop\CIPHER\annotation_packets`. No human submission received yet.
- 13:35 Several Ollama models (gpt-oss:20b, gemma4, MTP variants) disappeared from the local store between 13:05 and
  13:35; qwen3.6:35b-a3b (digest a7eb95c5) remains and is the primary model.
- 13:40-13:55 Practice smoke test: B1, B2, B1R ran 6/6 authored items without failures; ~20-90 s per case.
- 13:50 CI (GitHub Actions) green: fixtures, provenance, offline replay, stale-output check, paper compile, site build.
- 13:55 Calibration dev1: B2 labelled 8/14 calibration cases "Insufficient evidence". Traces show the extraction's
  boolean `evidence_sufficient` was set to false while the model's own note said the meaning was fully clear
  (K102, K201, K201v, K203v). Diagnosed as a schema-design defect, not a labelling disagreement (no human calibration
  labels existed). Fix: enum `evidence_status` (sufficient/insufficient) with the handbook's step-1 wording, which B1 and
  the annotators already receive. dev1 outputs are preserved; dev2 re-runs B2 on calibration.
- 15:13 Freeze 3; v2 held-out runs started. 15:19-~16:20 the author's own `rabt-ai serve` process shared the GPU and
  slowed inference about sixfold (latency in this window is not comparable; calls and tokens are unaffected).
- 16:22 v2 B0 and B1 complete (81/81 each, 0 errors).
- 17:29 The laptop went to sleep (Windows Kernel-Power event 42) while this session was idle; v2 B2 stopped at 77/81.
  19:19 resume. 19:20-19:22 Ollama auto-updated itself from 0.40.6 to 0.40.7; model digest unchanged (a7eb95c5).
  19:23 runs resumed with `runs/run_resume_v2.sh`, which logs the runtime version before each segment
  (`runs/sealed/runtime_versions.jsonl`). B0, B1 and 77 B2 cases ran on 0.40.6; the remaining 4 B2 cases, B1R and the
  secondary runs on 0.40.7.
