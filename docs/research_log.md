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
