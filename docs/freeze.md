# Freeze record

A freeze is a git commit plus the SHA-256 values below. It is internal, not an external preregistration.

## Freeze 1: corpus, cases, handbook, packets (2026-10-21, before any model run on evaluation cases)

| Artifact | SHA-256 (LF line endings) |
|---|---|
| `data/discovery/context_files.csv` (Zenodo 20090356) | e5dd3043ee098fcd36d71cbdc6232fae62bcc013971dcd536e36fe7d588840fc |
| `data/cases/manifest.json` (95 cases) | 4ff2cc31b10d1f2f2d996468445eca32e9f32b334a98e73aaa57c03ec1e7f177 |
| Packet JSON body, calibration A1 / A2 | see `annotations/keys/CIPHER-calibration_A*.json` (`packet_sha256`) |
| Packet JSON body, evaluation A1 / A2 | see `annotations/keys/CIPHER-evaluation_A*.json` (`packet_sha256`) |
| `docs/annotation_handbook.md` v1.0 | recorded in every packet as `handbook_version` |

Note: the first commit recorded the manifest hash of a CRLF copy (973628f5...f916). The content is byte-for-byte the
same JSON after line-ending normalisation (verified by parsing both); 4ff2cc31...f177 is the canonical LF hash.

## Freeze 2: methods (to be completed before held-out runs)

Profile text (`src/cipher/profile.py`), prompts (`configs/prompts/*.txt`), schemas and resolution rules
(`src/cipher/methods.py`), retry policy and decoding settings (`src/cipher/llm.py`), analysis plan
(`docs/analysis_plan.md`). Hashes are written into each run's `run_manifest.json`.

Freeze 2 recorded 2026-10-21 14:17 Asia/Dubai, before any held-out run:

| File | SHA-256 |
|---|---|
| `src/cipher/profile.py` | fa230bde257d3f40560c482446a56782f879557691a607f652a61c337b6b06c0 |
| `src/cipher/methods.py` | c517c3d726546ef37445dbaf9805373810d0a85b01aafef71f491c437062ce43 |
| `src/cipher/llm.py` | 1e1727a5b4ab838d13eccc65c5de53a40cbec8ca7ab6a1776f005c7a420bde1a |
| `src/cipher/run.py` | 1cd373f0303d5a79f3f0d3794c78b6f5a5f2bce5ef1066d0f1ef528de6e70d00 |
| `src/cipher/metrics.py` | 79890247041e881d8e42b9a852a514a03f75858f1b6942a8a91bd71d95fd5406 |
| `configs/prompts/common_guidance.txt` | 24558e679fbe8905b816678511e911505fcc05049a9eabeb9657e11b4b97d3b1 |
| `configs/prompts/b1_system.txt` | 54bf4ee86bce75b691a91ce620ea82fdf24a55565db7ea1ed8b2d450962d16b3 |
| `configs/prompts/b1r_review_system.txt` | 364901ada44ed7bfa8197598ea55420091f8e835f2b5be3717f8901119d14aed |
| `configs/prompts/b2_extract_system.txt` | fb72bf2106e78cb5a9f2edfd3b3a5e769b64777cf4f5f98f8c4d94aeae83c524 |
| `configs/prompts/b2_compare_system.txt` | 375464c29f2643f391538bb2c2e98ce07fa9ccd72486cefb892840e9b652215b |
| `docs/analysis_plan.md` | d17d40d52e293240d3913416751dd46c89bbdeb511c772af871a6e3e4e1c1436 |
| `docs/annotation_handbook.md` | 4ac46bf2c8ceb3f93fcf79ee2db2186e768b8602485e6a6fdfc5b39b3755f2e2 |
| `data/cases/manifest.json` | 4ff2cc31b10d1f2f2d996468445eca32e9f32b334a98e73aaa57c03ec1e7f177 |

## Freeze 3: corrected model input (recorded 2026-10-21 15:13 Asia/Dubai, before any held-out prediction was inspected)

An independent AI review found that the evidence header claimed every scope statement came from "the loaded files", although the keyword scan also covers the two instructions' own files, which may be off the target's chain (13 of 54 annotated evaluation cases). The header was corrected in `render_packet`; sealed runs no longer print per-case call or token counts; run manifests now record code hashes and model quantization. The v1 held-out runs (B0 and B1 complete, B2 partial) were stopped, were never inspected, and are kept unopened in `runs/sealed/heldout-v1-*` as superseded. All arms are re-run as v2.

| File | SHA-256 |
|---|---|
| `src/cipher/profile.py` | fa230bde257d3f40560c482446a56782f879557691a607f652a61c337b6b06c0 |
| `src/cipher/methods.py` | b91e0d08c734646c3c219f3d51426e6b605b9f9218afc9b456e5f0d382c48089 |
| `src/cipher/llm.py` | 1e1727a5b4ab838d13eccc65c5de53a40cbec8ca7ab6a1776f005c7a420bde1a |
| `src/cipher/run.py` | a64021902b98223829df705723de1d7226d938d3519e4dff9673b4afb6038408 |
| `src/cipher/metrics.py` | 79890247041e881d8e42b9a852a514a03f75858f1b6942a8a91bd71d95fd5406 |
| `configs/prompts/common_guidance.txt` | 24558e679fbe8905b816678511e911505fcc05049a9eabeb9657e11b4b97d3b1 |
| `configs/prompts/b1_system.txt` | 54bf4ee86bce75b691a91ce620ea82fdf24a55565db7ea1ed8b2d450962d16b3 |
| `configs/prompts/b1r_review_system.txt` | 364901ada44ed7bfa8197598ea55420091f8e835f2b5be3717f8901119d14aed |
| `configs/prompts/b2_extract_system.txt` | fb72bf2106e78cb5a9f2edfd3b3a5e769b64777cf4f5f98f8c4d94aeae83c524 |
| `configs/prompts/b2_compare_system.txt` | 375464c29f2643f391538bb2c2e98ce07fa9ccd72486cefb892840e9b652215b |
| `docs/annotation_handbook.md` | 4ac46bf2c8ceb3f93fcf79ee2db2186e768b8602485e6a6fdfc5b39b3755f2e2 |
| `data/cases/manifest.json` | 4ff2cc31b10d1f2f2d996468445eca32e9f32b334a98e73aaa57c03ec1e7f177 |

## Freeze 3b: analysis code (recorded 2026-10-21 15:18 Asia/Dubai, before any held-out prediction was inspected)

Applies addendum A1 of the analysis plan (review findings 6-13): pending mode reads no model output; variants require the human transformation check; model-produced anchors only, whole-range check; execution breakdown; illustrative-case rule; secondary-model path; unlock records analysis-code hashes.

| File | SHA-256 |
|---|---|
| `analysis/results.py` | f414763a3df9a5f8042c13ce72fbe86b6aba5191a480f994e16d4a5ea5c0ea67 |
| `src/cipher/metrics.py` | 79890247041e881d8e42b9a852a514a03f75858f1b6942a8a91bd71d95fd5406 |
| `src/cipher/reference.py` | b71b8131d1f4ab40e4ee88c54d065bda9c5ae714df45d89a56e6c03a9a1baeda |
| `src/cipher/unlock.py` | d5bd0701b1240bf008c13b2f8bfdd7e688a52ca7e17453e8f9d2a1b2bf209ab5 |
| `docs/analysis_plan.md` | d93e335a7713ae1e6edd860bb451d79bf3aa17cfffb69c50949869e8995dcb1d |

## Freeze 4: label-free analysis (recorded 2026-10-21 21:14 Asia/Dubai, before any held-out prediction was inspected)

No human labels will exist for this submission (author's decision, about 21:05). Analysis plan addendum A2 and the code below define the reported analysis. `analysis/results.py` (human-label analysis) is kept unchanged for future use.

| File | SHA-256 |
|---|---|
| `analysis/labelfree.py` | 6ee32682c02918ded8856197a23c8d2a312a1a3b90647ed8e6b92c32ae59328b |
| `src/cipher/unlock_labelfree.py` | f71e34dd541bcb8943f3395f6513ba8e122cfcf238763ca4719dbe26f46ab62a |
| `src/cipher/metrics.py` | 79890247041e881d8e42b9a852a514a03f75858f1b6942a8a91bd71d95fd5406 |
| `src/cipher/profile.py` | fa230bde257d3f40560c482446a56782f879557691a607f652a61c337b6b06c0 |
| `docs/analysis_plan.md` | 3ee733a849370b81ff7bc0fcae190c7c5c10ff3e4143bae6d18d725c7a40ce09 |

## Freeze 4a: presentation-only change after unsealing (recorded 2026-10-21 21:18 Asia/Dubai)

Figure 1 legend was clipped. `analysis/labelfree.py` changed only in `figure()` (legend placement; legend lists only labels that occur). `analysis/exports/metrics.json` is byte-identical before and after (verified with cmp).

| File | SHA-256 |
|---|---|
| `analysis/labelfree.py` | 46eff913ccac61c7fe416e8c734b7c3e84ff3d71d4d2a68c5ccd2f330d6f84d1 |
