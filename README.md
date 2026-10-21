# CIPHER: Contextual Instruction Precedence and Hierarchy Evaluation for Repositories

Research artifact for a short paper submitted to TEXTUAL 2027 (workshop at SANER 2027), EasyChair submission 162.
Authors: Awaiz Ahmed, Mohammad Umar, Huda Mueen (Al Ain University, United Arab Emirates).

Website: https://4waiz.github.io/cipher/ · Paper page: https://4waiz.github.io/cipher/paper/

## What this studies

Repository instruction files such as `AGENTS.md` guide AI coding agents, and a nested file may legitimately refine or
replace guidance from its ancestors. Two instructions that look contradictory can be a real conflict, a valid local
override, or not jointly applicable to the task at all. CIPHER labels each case, one instruction pair plus one concrete
task and target file at a pinned commit, with one of five labels under a declared loading profile:

| Label | Meaning |
|---|---|
| Unresolved conflict | Both hard requirements are in force for the same decision and nothing picks a winner. |
| Valid override | Both apply, they are incompatible, and the profile or an explicit statement picks a winner. |
| Disjoint applicability | Before priority, at least one instruction is inactive for this target or task. |
| Compatible | Everything in force can be satisfied together. |
| Insufficient evidence | The material cannot establish meaning, applicability, or precedence. |

It compares B0 (a pairwise adaptation of Ruleherd's keyword heuristics), B1 (a direct model with the full evidence),
B2 (the CIPHER structured pipeline: model-based extraction + deterministic ancestry and precedence + a model
incompatibility check), and B1R (an equal-call self-review control), all with one local open-weight model.

## Status

See `docs/PROGRESS.md` for the current state. Human reference labels come only from the authors' independent
annotations and adjudication; held-out model predictions stay sealed (`runs/sealed/`, not committed) until the labels
are final. No accuracy number is reported without final human labels. This is a small pilot; see Limitations.

## Repository layout

| Path | Contents |
|---|---|
| `src/cipher/` | Implementation: profile, Markdown spans, acquisition, candidate retrieval, cases, packets, methods, model adapter, metrics, reference labels |
| `tests/` | Engineering fixtures (not research data) |
| `configs/` | Frozen prompts (`configs/prompts/`), held-out run IDs |
| `data/` | Discovery table, pinned AGENTS.md snapshots (JSON), case manifest, selection and acquisition logs |
| `annotations/` | Packets, ID keys, genuine submissions, adjudication, reference labels, agreement |
| `runs/` | Run outputs: `dev/` (calibration and practice), `heldout/` (unlocked held-out runs) |
| `analysis/` | Corpus statistics, results computation, exported tables and JSON |
| `paper/` | Manuscript source (`body.tex`), bibliography, build script |
| `site/` | Static website (`python site/build.py`) |
| `docs/` | Protocol, handbook, analysis plan, freeze record, logs, related-work audit, AI-assistance record |

## Reproducibility

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/). Paper builds need [Tectonic](https://tectonic-typesetting.github.io)
(0.17.0 was used). Fresh model inference needs [Ollama](https://ollama.com) with `qwen3.6:35b-a3b`
(digest `a7eb95c53bcf…`) and a GPU; the saved outputs make inference optional.

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv -e ".[dev]" pypandoc_binary==1.15
.venv/bin/python -m pytest                       # engineering fixtures
```

### Offline replay of the reported results (no model, no network)

```bash
.venv/bin/python analysis/corpus_stats.py        # corpus macros and corpus.json
.venv/bin/python analysis/results.py             # metrics, tables, figure, site exports from saved runs and labels
.venv/bin/python paper/build.py                  # named and anonymous PDFs, HTML fragment, page renders
.venv/bin/python site/build.py                   # static site in site/dist/
```

### Rebuilding inputs (network; results may differ if upstream repositories changed)

```bash
.venv/bin/python -m cipher.acquire --max-repos 30   # GitHub API via an authenticated `gh` CLI; pinned commits recorded
.venv/bin/python -m cipher.cases                    # deterministic case manifest from the stored snapshots
.venv/bin/python -m cipher.annotate                 # blinded annotation packets (HTML)
```

### Fresh inference (needs Ollama and the pinned model; outputs can vary across hardware and versions)

```bash
.venv/bin/python -m cipher.run --method B0  --split evaluation --run-id my-b0
.venv/bin/python -m cipher.run --method B1  --split evaluation --run-id my-b1
.venv/bin/python -m cipher.run --method B2  --split evaluation --run-id my-b2
.venv/bin/python -m cipher.run --method B1R --split evaluation --run-id my-b1r
```

Each run writes `predictions.jsonl` and `run_manifest.json` (model digest before and after, decoding settings,
prompt hashes, code commit, package versions, token counts, latency, retries, failures).

### Reference labels

```bash
.venv/bin/python -m cipher.reference status        # submissions received
.venv/bin/python -m cipher.reference adjudication  # agreement + adjudication packet (after both submissions)
.venv/bin/python -m cipher.reference review        # transformation-validity checklist
.venv/bin/python -m cipher.reference finalize      # reference_labels.json
```

## Data and licences

Code: MIT (`LICENSE`). Mined AGENTS.md text remains under each source repository's licence; see `DATA_LICENSE.md`.
The discovery table is from Galster et al., CC BY 4.0 (Zenodo 10.5281/zenodo.20090356). Mined instructions are
stored as inert JSON and are never executed or followed.

## Limitations

Small, challenge-oriented sample (8 evaluation repositories) that cannot estimate how often conflicts occur;
researcher-authored tasks; constructed variants; annotators are the authors; one declared profile and one quantized
model; classification only, no claim about agent behaviour or code quality.

## AI assistance

ChatGPT (OpenAI) helped draft the October 2026 proposal. Claude (Anthropic, Claude Code) implemented the pipeline,
collected the corpus, built the annotation tools, ran the models, computed the analysis, and drafted the manuscript and
website under the authors' direction. Neither system produced any human reference label. Details:
`docs/ai_assistance.md`.

## Citation

See `CITATION.cff`. The paper is under review; no acceptance, DOI, or indexing is claimed.
