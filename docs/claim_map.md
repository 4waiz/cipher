# Claim-to-evidence map

Every factual claim in the manuscript and website, with the evidence that supports it. Numbers in the paper are LaTeX
macros generated from the files named here; prose claims cite a source file or an external source verified in
`docs/related_work.md`.

| Claim (paper section) | Evidence |
|---|---|
| AGENTS.md says "the closest AGENTS.md to the edited file wins" (I) | agents.md FAQ, quoted in `docs/related_work.md` [1]; re-checked 2026-10-21 |
| Configuration Smells: 28 detected, 16 confirmed by that study's first author, 100 repositories (I) | arXiv:2606.15828v5 §VI-F p.7, quoted in `docs/related_work.md`; re-checked 2026-10-21 |
| Ruleherd compares files with keyword/polarity heuristics, no scope logic (I, V) | Ruleherd README and `bin/ruleherd.mjs` at commit 94559fc6 (`checkConflicts`) |
| WIRE reports no matched compatible-pair or priority-insertion controls (II) | arXiv:2605.27784v2 §5, quoted in `docs/related_work.md` |
| Guidefold resolves most-specific scope; human-labelled conflicts still zero (II) | Guidefold RESEARCH.md at 1c98b24f §5.3, quoted in `docs/related_work.md` |
| McMillan: no detectable effect of injected contradictions (II) | arXiv:2605.10039v1 abstract, quoted in `docs/related_work.md` |
| Frame of 237 repositories; 30 retrieved; 24 snapshot-eligible; 12 pair-eligible (IV) | `analysis/corpus_stats.py` -> `paper/generated/corpus.tex`; `data/acquisition_log.json`; `data/cases/selection_log.json` |
| 27 originals (16 ancestor-descendant, 5 unrelated, 6 same-file), 27 variants (16 target, 11 placement), 27 controls (IV) | `data/cases/manifest.json` via `analysis/corpus_stats.py` |
| Annotation procedure, blinding, calibration of 20 items with 6 practice items (IV) | `src/cipher/annotate.py`, `annotations/packets/`, `annotations/keys/`, `docs/annotation_handbook.md` |
| B0/B1/B2/B1R definitions and budgets (V) | `src/cipher/methods.py`, `configs/prompts/`, run manifests |
| Model and decoding settings (V) | `src/cipher/llm.py` (`ModelConfig`), each `run_manifest.json`; model card (Hugging Face, Qwen/Qwen3.6-35B-A3B) |
| Freeze before held-out runs; predictions sealed until labels final (V) | `docs/freeze.md`, git history, `runs/heldout/UNLOCK.json` |
| All results numbers (VI) | `analysis/results.py` -> `analysis/exports/metrics.json` -> `paper/generated/results.tex`, `tab_*.tex` |
| Human agreement (VI) | `annotations/agreement.json` from the two genuine submissions |
