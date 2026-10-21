# Data licences

The MIT licence in `LICENSE` covers the code in this repository and the authors' own documentation. It does **not**
relicense third-party text.

- `data/snapshots/*.json` and the evidence inside `data/cases/`, `annotations/packets/`, and run outputs contain
  verbatim AGENTS.md text from public GitHub repositories. Each file remains under the licence of its source
  repository, recorded in its snapshot (`license`, SPDX identifier) together with the repository, commit, path, Git blob
  SHA and SHA-256. Only repositories with an open-source licence detected by GitHub were sampled. Licences of the
  repositories used in the study: BSD-2-Clause (dartsim/dart), Apache-2.0 (SEMOSS/semoss-ui, marin-community/marin,
  zenml-io/zenml, opsmill/infrahub-sdk-python), MIT (cypress-io/cypress, tryghost/ghost), AGPL-3.0
  (TracecatHQ/tracecat, RSSNext/Folo), BSD-3-Clause (appwrite/appwrite). Snapshots of other repositories retrieved
  during sampling carry their own recorded licences.
- `data/discovery/context_files.csv` and `0_README_zenodo.md`: M. Galster et al., "A Dataset of Agentic AI Coding Tool
  Configurations", Zenodo 10.5281/zenodo.20090356, CC BY 4.0.
- `paper/ieee.csl`: Citation Style Language project, CC BY-SA 3.0 (source commit in `paper/ieee.csl.SOURCE`).
- Human annotations, adjudications, and reference labels by the authors: CC BY 4.0.

To re-retrieve the original files instead of using the stored copies, run `python -m cipher.acquire`; the stored
commit SHAs and blob SHAs let you verify that you obtained identical bytes.
