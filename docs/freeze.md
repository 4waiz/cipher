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
