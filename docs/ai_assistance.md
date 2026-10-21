# AI-assistance record

IEEE requires disclosure of AI-generated content in the Acknowledgments, naming the system, the affected sections,
and the level of use (IEEE Author Center, Submission Policies, accessed 2026-10-21).

| System | When | What it did | What it did not do |
|---|---|---|---|
| ChatGPT (OpenAI) | Oct 2026, before 18 Oct | Concept exploration, literature synthesis, and drafting of the original proposal, abstract, and guide (archived in `docs/archive/proposal-2026-10-18/`) | No data, labels, or results |
| Claude Opus 5.5 via Claude Code (Anthropic) | 21-23 Oct 2026 | Verified venue rules; ran a related-work audit with a subagent; wrote all code in `src/`, `analysis/`, `paper/build.py`, `site/`; retrieved and sampled the corpus; authored the task templates, practice items, and handbook text; ran all model arms; computed all results; drafted the manuscript text, figures, tables, and website | Did not annotate, adjudicate, or approve anything; produced no human reference label; did not act as an evaluation model (all evaluated predictions come from a separate local model through clean API requests) |
| Qwen3.6-35B-A3B (local, Ollama) | 21-22 Oct 2026 | The model evaluated in B1, B2, and B1R | Saw only method prompts and evidence packets |

Human annotation: none was performed for version 1.0.0 (the authors decided on 21 Oct 2026 not to annotate before the
deadline). No AI output was used as a reference label. The human authors are responsible for reviewing and approving
the manuscript before submission. Entries here are updated only when the corresponding human action
has actually happened (see `docs/PROGRESS.md`).
