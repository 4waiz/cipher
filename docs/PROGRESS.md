# CIPHER progress file

Resume point after any context reset. Update at every milestone.

Last updated: 2026-10-21 13:20 Asia/Dubai

## Hard dates

- Paper deadline: 23 Oct 2026 AoE = 24 Oct 2026 15:59 Asia/Dubai. Team upload target: 23 Oct (UAE).
- EasyChair Submission 162 (TEXTUAL track, saner27tracks). Do not create a new record. Do not click Submit for the author.

## State

| Item | Status |
|---|---|
| Original proposal package | Archived in `docs/archive/proposal-2026-10-18/` (unchanged) |
| Venue rules | Verified except anonymity/references/preprint policy (`docs/venue_requirements.md`) |
| Toolchain | Python 3.12 + uv; Tectonic 0.17.0 in `../.tools/tectonic/`; Ollama 0.40.6 with local models; gh as 4waiz |
| Model access | No Anthropic/OpenAI API key in environment. Local Ollama models on RTX 5080 16 GB. No spending. |
| Discovery corpus | Galster et al. context_files.csv (Zenodo 20090356) in `data/discovery/` |
| Cases | Not yet collected |
| Annotation packets | Not yet built |
| Human labels | None received |
| Model runs | None |
| Paper | Proposal draft only |
| GitHub repo | 4waiz/cipher does not exist yet |

## Next executable action

Write `src/cipher/acquire.py`: sample repositories from the discovery corpus with a recorded seed, pin HEAD commits,
retrieve every AGENTS.md at that commit through the GitHub API, store snapshots as inert JSON.
