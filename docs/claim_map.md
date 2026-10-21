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
| All results numbers (VI), abstract, Table I, Fig. 1 | `runs/heldout/heldout-v2-*` (hashes in `runs/heldout/UNLOCK.json`) -> `analysis/labelfree.py` -> `analysis/exports/metrics.json` -> `paper/generated/results.tex`, `tab_results.tex`, `paper/build/figures/labels.pdf` |
| "four of 27 controls changed" (abstract, VI) | 27 minus `\BOneOrderStable`, `\BTwoOrderStable`, `\BOneROrderStable` (23 each) |
| Profile-determined reference = Disjoint for 26 cases (VI) | `analysis/labelfree.py:profile_determined` using `cipher.profile.loaded_set`; addendum A2 |
| B0's two PD flags are one ESM/CommonJS match (E203, E203c) (VI) | `runs/heldout/heldout-v2-B0/predictions.jsonl` (`topic`: "module system") |
| Illustrative case E102 and both explanations (VI) | `metrics.json` `illustrative`; `runs/heldout/heldout-v2-B1|B2/predictions.jsonl` for E102 |
| No failures, retries or malformed outputs (VI) | `metrics.json` `execution` per method |
| Analysis frozen before predictions were opened (V, VI) | `docs/freeze.md` Freeze 4 (commit 5c006d6) precedes `runs/heldout/UNLOCK.json` (17:14 UTC) |
| Ollama 0.40.6 / 0.40.7 split (V) | `docs/research_log.md`, `runs/sealed/runtime_versions.jsonl` (local) |
| No human labels; RQ1 not answered (IV, VI, VII) | `docs/decision_log.md` D18; `annotations/submissions/` is empty |
