# CIPHER related-work audit

Accessed: 21 October 2026, for every source. Checked against primary pages: arXiv abs, HTML and PDF of the exact version; ACL Anthology; Crossref for ACM DOIs; the Zenodo API; the GitHub API; and the official SCAM 2026 program. No third-party PDFs are stored in the project. Page numbers refer to the cited arXiv PDF unless proceedings pages are given.

## Verified bibliography

**[1]** "AGENTS.md." [Online]. Available: https://agents.md/ (accessed Oct. 21, 2026).
Status: format documentation, undated and unversioned. Exact text:
- Under "4. Large monorepo? Use nested AGENTS.md files for subprojects": "Place another AGENTS.md inside each package. Agents automatically read the nearest file in the directory tree, so the closest one takes precedence and every subproject can ship tailored instructions."
- FAQ "What if instructions conflict?": "The closest AGENTS.md to the edited file wins; explicit user chat prompts override everything."
- Caveat: the page does not say whether ancestor files are also read or merged. "Ancestors apply unless overridden" is CIPHER's interpretation.

**[2]** W. Chatlatanagulchai, H. Li, Y. Kashiwa, B. Reid, K. Thonglek, P. Leelaprute, A. Rungsawang, B. Manaskasemsak, B. Adams, A. E. Hassan, and H. Iida, "Agent READMEs: An Empirical Study of Context Files for Agentic Coding," arXiv:2511.12884v2, Aug. 2026. [Online]. Available: https://arxiv.org/abs/2511.12884v2
Status: preprint. v2 (9 Aug 2026) is the latest. Discrepancy: none.

**[3]** H. V. F. dos Santos, V. Costa, J. E. Montandon, L. L. Silva, and M. T. Valente, "Configuration Smells in AGENTS.md Files: Common Mistakes in Configuring Coding Agents," in *Proc. 26th IEEE Int. Conf. Source Code Analysis and Manipulation (SCAM)*, 2026. arXiv:2606.15828v5. [Online]. Available: https://arxiv.org/abs/2606.15828v5
Status: peer-reviewed, accepted. The venue appears in the arXiv journal reference and in the official SCAM 2026 program (Research Track, 15 Sep 2026). No pages or DOI were found. v5 (30 Jul 2026) is the latest. Discrepancy: none.

**[4]** L. Yan, X. Chen, and X. Zhang, "WIRE: Profiling Witnessed Within-Policy Instruction Collisions in LLM Agents," arXiv:2605.27784v2, Jul. 2026. [Online]. Available: https://arxiv.org/abs/2605.27784v2
Status: preprint. v2 (26 Jul 2026) is the latest. Discrepancy: none. v1 was titled "Diagnosing Live Within-Policy Instruction Conflicts in LLM Agents with Witnessed Resolution Profiles".

**[5]** R. K. Sharma, "ContextCov: Bridging the Gap Between Developer Intent and Autonomous Agent Execution," arXiv:2603.00822v2, May 2026. [Online]. Available: https://arxiv.org/abs/2603.00822v2
Status: preprint. v2 (4 May 2026) is the latest. The manuscript bibliography uses the arXiv listing title ("ContextCov: Deriving and Enforcing Executable Constraints from Agent Instruction Files"), which both versions share.
Discrepancy: the arXiv *listing* title for both versions is "ContextCov: Deriving and Enforcing Executable Constraints from Agent Instruction Files". The prior citation's title is the one printed on the v2 manuscript; v1 printed the "Deriving…" title. Write "R. K. Sharma" with a period.

**[6]** D. Ding, S. Liu, E. Yang, J. Lin, Z. Chen, S. Dou, H. Guo, W. Cheng, P. Zhao, C. Xiao, Q. Zeng, Q. Zhang, X. Huang, Q. Xu, and T. Gui, "OctoBench: Benchmarking Scaffold-Aware Instruction Following in Repository-Grounded Agentic Coding," in *Proc. 64th Annu. Meeting Assoc. Comput. Linguistics (Vol. 1: Long Papers)*, San Diego, CA, USA, Jul. 2026, pp. 5958–5978, doi: 10.18653/v1/2026.acl-long.269.
Status: peer-reviewed. Preprint: arXiv:2601.10343v2. Discrepancy: none; add the DOI.

**[7]** wiatrM, "Guidefold: docs/RESEARCH.md," GitHub, commit 1c98b24f8b6fc28a3a7253ab6dd9c3cc626f885e, Sep. 19, 2026. [Online]. Available: https://github.com/wiatrM/guidefold/blob/1c98b24f8b6fc28a3a7253ab6dd9c3cc626f885e/docs/RESEARCH.md
Status: project notes, not peer-reviewed; "Living synthesis, updated 2026-09-19"; Apache-2.0. It targets SKILL.md and guidance cards, not AGENTS.md.

**[8]** princejain756, "ruleherd," v0.1.3, GitHub, commit 94559fc6399a5fbf77c2f76f96172d2207d32e8d, Oct. 14, 2026, MIT License. [Online]. Available: https://github.com/princejain756/ruleherd
Status: software. The commit is one past tag `v0.1.3` (dd069cc) and changes only the repository URL in `package.json`, whose version is still 0.1.3.
- README: "Contradiction detection is heuristic. It catches keyword pairs (npm/pnpm, tabs/spaces, jest/vitest, ESM/CJS) and never/always polarity on shared topics like `commit`, `push`, `test`."
- Code: `checkConflicts` requires the two sides to be in different files. It has no applicability or precedence logic.

**[9]** M. Galster, S. Mohsenimofidi, L. Böhme, J. L. Lulla, M. A. Abubakar, C. Treude, and S. Baltes, "A Dataset of Agentic AI Coding Tool Configurations," in *Proc. 3rd ACM Int. Conf. AI-Powered Software (AIware '26)*, 2026, pp. 314–322, doi: 10.1145/3805760.3814922. arXiv:2605.08435v1. Data: Zenodo, doi: 10.5281/zenodo.19375880.
Status: peer-reviewed. The venue and pages come from the Crossref record for the ACM DOI.
Discrepancies:
- "Bohme" should be "Böhme"; add the pages and DOI.
- 19375880 is Zenodo's *concept* DOI, covering all versions. The latest version is 10.5281/zenodo.20090356 (7 May 2026).

Which paper is which:
- The Zenodo README's "Associated Papers" entry, "Configuring Agentic AI Coding Tools: An Exploratory Study", is a separate AIware '26 paper: pp. 11–20, doi: 10.1145/3805760.3814887, without Böhme.
- Its arXiv version, 2602.14690v5, is now titled "Harness Engineering for Agentic AI Coding Tools: An Exploratory Study".
- The dataset extends that study's data. The dataset website says to cite the dataset paper, [9].

**[10]** T. Gloaguen, N. Mündler-Sasahara, M. N. Müller, V. Raychev, and M. Vechev, "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?," arXiv:2602.11988v3, Sep. 2026. [Online]. Available: https://arxiv.org/abs/2602.11988v3
Status: preprint. v3 (29 Sep 2026) is the latest. Discrepancy: restore the umlauts.

**[11]** C. Treude and S. Baltes, "Context Rot in AI-Assisted Software Development: Repurposing Documentation Consistency for AI Configuration Artifacts," arXiv:2606.09090v1, Jun. 2026. [Online]. Available: https://arxiv.org/abs/2606.09090v1
Status: preprint. Only v1 exists. Discrepancy: add "v1".

**[12]** IEEE, "Submission Policies," IEEE Author Center Conferences. [Online]. Available: https://conferences.ieeeauthorcenter.ieee.org/author-ethics/guidelines-and-policies/submission-policies/ (accessed Oct. 21, 2026).

**Additional close work** (preprints, found through 3 web searches):
- **[A1]** D. McMillan, "Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure Variables," arXiv:2605.10039v1, May 2026.
- **[A2]** T. Mason, "Arbiter: Detecting Interference in LLM Agent System Prompts," arXiv:2603.08993v2, Oct. 2026.

No other work was found that classifies parent/child AGENTS.md conflicts using applicability and precedence.

## Comparison matrix

Column key: Scope = models applicability/scope; Prec. = models precedence/priority; Task = task-conditioned; Human = human reference labels; Controls = controlled variants or counterfactuals.

| Work | Artifact | Conflict notion | Scope? | Prec.? | Task? | Human? | Controls? | CIPHER must credit |
|---|---|---|---|---|---|---|---|---|
| [1] | AGENTS.md convention | conflicting instructions | nested files | closest wins; user overrides | edited file | – | – | the precedence rule |
| [2] | 2,303 root-level files | none | no (root only) | no | no | content coding | no | characterizing context files |
| [3] | 100 AGENTS.md/CLAUDE.md files | within-file contradiction | no | no | no | one rater confirms flags | no | conflicts as a known smell |
| [4] | 6 system-prompt policies | witnessed hard collision | activation conditions | none assumed | witness states | audit | none (no compatible-pair or priority controls) | grounded rules, activation, decision surfaces |
| [5] | instruction files | rule vs. local context | heading path | no | yes | 384-sample audit | baselines | path-aware scoped extraction |
| [6] | scaffolds incl. AGENTS.md | cross-source (user, system, docs) | no | measures implicit priority | yes | checklist audit | 32 single-pair conflicts | showing docs lose to system and user |
| [7] | SKILL cards | equal-scope disagreement leads to `ASK` | scope lattice | most specific wins | target leaf | 0 admitted | structural replays | prior scope-precedence resolver |
| [8] | instruction files | keyword/polarity across files | no | no | no | no | no | B0 |
| [9] | 15,591 artifacts | none | paths available | no | no | no | no | data source |
| [10] | context files | none | no | no | yes | no | with vs. without | context files' uncertain value |
| [11] | config files | staleness vs. code | no | no | no | inspection | no | consistency framing |
| [A1] | CLAUDE.md, AGENTS.md, nested files | injected inter-file contradiction | nested files | no | yes | no | factorial | controlled conflicts (null effect) |
| [A2] | 3 vendor system prompts | interference | scope overlap | priority ambiguity | no | 21 patterns | no | interference taxonomy |

## Verified quantitative statements

- **[3], §VI-F, p. 7:** "The proposed heuristic detected 28 cases of Conflicting Instructions. However, after a manual analysis conducted by the first author, only 16 cases were confirmed (57%)."
  - Table II (p. 6): 28 instances, 12 false positives, 57% precision. This is precision only, from one rater; recall is not reported.
  - Corpus (abstract): "we analyzed 100 popular open-source repositories containing either an AGENTS.md or a CLAUDE.md file".
  - Detector: gemini-3.1-flash-lite (§VI, p. 5). Its prompt receives one file (Fig. 4), so the conflicts found are within a single file.
- **[4], abstract:** "only 35.4% satisfy both governed rules" (1,402 witnesses, 13,335 trials). §5 Setup, pp. 5–6: "We do not include rule-removal, rule-reordering, priority-insertion, matched compatible-pair, or single-rule controls."
- **[6], §4.3.1, p. 5964:** "Overall, we observe a consistent hierarchy where SP dominates MD and UQ dominates MD". Here SP is the system prompt, UQ the user query and MD the project documentation. App. E, p. 5972: "OCTOBENCH-CONFLICT contains 32 instances".
- **[2], abstract:** "2,303 agent context files from 1,925 repositories". §3, p. 5: files were found by scanning "the root directory of each selected repository".
- **[10], abstract:** "providing context files does not generally improve task success rates, while increasing inference cost by over 20% on average."
- **[11], abstract:** stale references were found "in 23.0% of repositories" (n = 356). §3.3, p. 3: "36% of elements classified as stale were false positives or ambiguous on inspection".
- **[5], abstract:** "ContextCov achieves 88.3% constraint compliance (vs. 67.0% and 50.3%)". §3.5, p. 6: "Should it apply globally or only in certain directories?" The answer adopted is fail-closed and global.
- **[7], §5.3 "Label-free systems track":**
  - "All six checks passed for all 176 pairs across 11 repositories".
  - "This is algorithmic feasibility, not yet evidence on human-labelled conflicts."
  - "Human-accepted tasks and C1 admissions remain zero."
- **[A1], abstract:** "None of the four structural variables or three two-way interactions produces a detectable contrast after multiple-testing correction."

## Contribution boundaries

- **Applicability and precedence reasoning is not new.** See [1], [7]'s most-specific-source lattice, and [5]'s scoped extraction.
- **Detecting conflicts in instruction files is not new.** See [3], [8] and [A2]. Do not claim "first".
- **Grounded rule spans, activation conditions and witnessed collisions are not new** ([4]). Neither are measured cross-source resolution ([6]) or controlled nested-file conflicts ([A1]).
- **Do not claim these conflicts harm agents.** [10] and [A1] argue against assuming it, and CIPHER does not measure agent behavior. Do not generalize [3]'s single-rater 57% to cross-file pairs.
- **Defensible contribution:** a small, human-labeled study of *apparent* conflicts between real nested AGENTS.md pairs. It tests whether making target-path applicability and nested precedence explicit (B2) changes five-way classification relative to a keyword heuristic (B0) and a full-evidence LLM (B1).
  - The gap is narrow: no audited work provides human labels that separate valid override and disjoint applicability from true conflict in mined AGENTS.md hierarchies.
  - [7] had zero human admissions at the cited commit, and [4] lacks compatible-pair controls.

## IEEE AI disclosure

From [12], under "Guidelines for Artificial Intelligence (AI)-Generated Text":

> "The use of content generated by artificial intelligence (AI) in an article (including but not limited to text, figures, images, and code) shall be disclosed in the acknowledgments section of any article submitted to an IEEE publication. The AI system used shall be identified, and specific sections of the article that use AI-generated content shall be identified and accompanied by a brief explanation regarding the level at which the AI system was used to generate the content."

What it requires:
- The disclosure goes in the Acknowledgments section.
- It names the AI system.
- It names the specific sections containing AI-generated text, figures, images or code.
- It gives a brief explanation of the level of AI use.
- Editing and grammar help alone: disclosure "is not required, but recommended". If an AI system is used for editing, "exclude the reference section".
