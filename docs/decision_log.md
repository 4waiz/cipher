# Decision log

Material decisions, with reasons. Newest last. Times are Asia/Dubai.

## 2026-10-21

**D1 13:15. Paper category: Short / Vision (up to 4 pages).** The official TEXTUAL page lists Full (8), Short/Vision (4),
Tool & Dataset (4). A two-day pilot with a small human-labeled sample is "preliminary empirical results", not a "thorough
empirical investigation". Page budget: 4 pages including references, the strictest reading of an unstated rule.

**D2 13:15. Named-author PDF is the default; anonymous PDF kept as fallback.** No anonymity rule is stated in the TEXTUAL
call. The SANER main-track double-blind rule is not substituted. Final designation stays conditional on EasyChair or
organizer instructions.

**D3 13:15. Inference uses local open-weight models through Ollama; no paid API.** No API key is configured. The Claude
Code session's own authentication is not an evaluation API and this conversation has seen research material, so it must
not serve as an evaluation context. Local models on the author's RTX 5080 cost nothing, are pinned by Ollama digest, and
are called through clean HTTP requests containing only the allowed evidence and the method prompt.

**D4 13:15. Discovery source: Galster et al. dataset, context_files.csv, Zenodo record 20090356 (latest version of
DOI 10.5281/zenodo.19375880), SHA-256 e5dd3043...840fc.** A row is a lead only; every file is re-retrieved at a pinned
commit through the GitHub API.

**D5 13:15. B0 is an attributed pairwise adaptation of Ruleherd v0.1.3 (MIT, commit 94559fc6).** Ruleherd reports
repository-level CONFLICT findings from TOPIC_PAIRS lexicons and never/always polarity across different files. The
adaptation applies the same regular expressions to the two spans of one case and outputs a binary conflict flag. It is
scored only on binary conflict metrics.

**D6 13:15. LaTeX engine: Tectonic 0.17.0 (official GitHub release), kept outside the repository in `.tools/`.** No TeX
distribution was installed. Tectonic resolves IEEEtran from the TeX Live bundle.

**D7 13:30. Frozen pilot: 27 evaluation originals from 8 repositories (target was 32; four repositories yielded fewer
than four selectable pairs), one context variant and one order control each.** No case was invented to reach the target.

**D8 13:40. Order controls are not annotated; they inherit the parent's final label after a human check that only the
presentation order changed.** This keeps the independent annotation load at 54 evaluation items (about two hours) while
still giving RQ3 a stability test. Variants are annotated independently because their label may change.

**D9 13:40. Annotators A1 = Awaiz Ahmed, A2 = Mohammad Umar; adjudicator = Huda Mueen** (as suggested in the brief;
subject to the authors' actual participation, which is recorded only when files arrive).

**D10 13:40. Primary model: qwen3.6:35b-a3b (Q4_K_M) via Ollama, thinking on, temperature 0.6, top-p 0.95, top-k 20,
seed 20261021, num_ctx 16384, num_predict 8192, two retries with seed+1/+2.** gpt-oss:20b and gemma4 disappeared from
the local Ollama store during the session, so they are not used. Qwen's recommended thinking-mode sampling is used
instead of greedy decoding to avoid repetition loops; the fixed seed makes runs repeatable on this machine.

**D11 13:42. B2 makes the second (incompatibility) call only when both instructions remain active and binding; B1R is
added as an equal-call control.** Calls, tokens and latency are reported per arm.

**D12 13:45. Evidence packets for models contain the spans, their enclosing sections, the list of AGENTS.md paths, and
keyword-scanned scope statements; annotators could also expand the two full files.** The asymmetry is reported;
annotators can flag missing context.

**D13 13:50. Venue category check: TEXTUAL page lists no anonymity rule; named PDF default, anonymous PDF fallback.
Repository stays private until the end of the task, then becomes public with Pages, because no stated rule restricts a
public artifact.**

**D14 14:05. B2 extraction schema change before any held-out run: boolean `evidence_sufficient` replaced by enum
`evidence_status` with the handbook's step-1 wording.** Calibration traces showed the boolean contradicting the model's
own explanation in 5 of 14 cases. This corrects an interface defect; it was not fitted to reference labels (none existed).
