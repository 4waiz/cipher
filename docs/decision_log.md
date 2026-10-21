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
