"""Discovery frame and pinned snapshot acquisition.

Discovery source: Galster et al., "A Dataset of Agentic AI Coding Tool Configurations", context_files.csv from
Zenodo record 20090356. A row is only a lead: every AGENTS.md is re-retrieved from GitHub at one pinned commit.

Snapshots are stored as JSON so that mined AGENTS.md text can never configure a coding tool that opens this repository.
Retrieval uses the authenticated GitHub CLI (`gh api`); nothing from the sampled repositories is executed.
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import json
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_CSV = ROOT / "data" / "discovery" / "context_files.csv"
DISCOVERY_SHA256 = "e5dd3043ee098fcd36d71cbdc6232fae62bcc013971dcd536e36fe7d588840fc"
SNAP_DIR = ROOT / "data" / "snapshots"
SEED = 20261021

# Nested files under these directory names configure separate project roots (templates, examples, vendored code,
# tool-specific skill folders) and fall under the excluded "multiple working roots" condition.
EXCLUDED_DIR_PARTS = {"templates", "template", "examples", "example", "deps", "vendor", "vendored", "third_party",
                      "node_modules", "_vendored", "fixtures", "testdata"}
PERMISSIVE = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0", "0BSD", "Unlicense",
              "CC0-1.0", "EPL-2.0", "LGPL-2.1", "LGPL-3.0", "GPL-2.0", "GPL-3.0", "AGPL-3.0", "BSL-1.0", "Zlib",
              "MIT-0", "Artistic-2.0", "PostgreSQL", "EUPL-1.2", "CC-BY-4.0"}
MIN_NONEMPTY_LINES = 5


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def eligible_path(path: str) -> bool:
    parts = path.split("/")
    if parts[-1] != "AGENTS.md":
        return False
    for d in parts[:-1]:
        if d.startswith(".") or d.lower() in EXCLUDED_DIR_PARTS:
            return False
    return True


def build_frame() -> list[str]:
    """Repositories whose dataset rows show a root AGENTS.md and at least one eligible nested AGENTS.md
    (neither a pointer file), returned in a seeded random order."""
    data = DISCOVERY_CSV.read_bytes()
    if sha256_bytes(data) != DISCOVERY_SHA256:
        sys.exit("discovery CSV hash mismatch")
    rows = list(csv.DictReader(data.decode("utf-8").splitlines()))
    by_repo: dict[str, list[dict]] = {}
    for r in rows:
        if r["context_file"].split("/")[-1] == "AGENTS.md" and r["is_reference"] == "False":
            by_repo.setdefault(r["repo_name"], []).append(r)
    frame = []
    for repo, rs in by_repo.items():
        paths = {r["context_file"] for r in rs}
        nested = [p for p in paths if "/" in p and eligible_path(p)]
        if "AGENTS.md" in paths and nested:
            frame.append(repo)
    frame.sort(key=str.lower)
    random.Random(SEED).shuffle(frame)
    return frame


def gh(path: str) -> dict | list:
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(f"gh api {path}: {out.stderr.strip()[:200]}")
    return json.loads(out.stdout)


def snapshot(repo: str) -> dict:
    """Retrieve every eligible AGENTS.md at the current default-branch HEAD and record provenance."""
    meta = gh(f"repos/{repo}")
    branch = meta["default_branch"]
    commit = gh(f"repos/{repo}/commits/{branch}")["sha"]
    tree = gh(f"repos/{repo}/git/trees/{commit}?recursive=1")
    entries = tree["tree"]
    symlinked = [e["path"] for e in entries if e["path"].endswith("AGENTS.md") and e["mode"] == "120000"]
    agents = [e for e in entries if e["type"] == "blob" and e["mode"] != "120000" and eligible_path(e["path"])]
    files = []
    for e in sorted(agents, key=lambda e: e["path"]):
        blob = gh(f"repos/{repo}/git/blobs/{e['sha']}")
        raw = base64.b64decode(blob["content"])
        files.append({"path": e["path"], "blob_sha": e["sha"], "sha256": sha256_bytes(raw),
                      "content": raw.decode("utf-8", errors="replace")})
    return {
        "repo": repo,
        "commit": commit,
        "default_branch": branch,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "license": (meta.get("license") or {}).get("spdx_id"),
        "fork": meta.get("fork"),
        "archived": meta.get("archived"),
        "tree_truncated": tree.get("truncated", False),
        "symlinked_agents_md": symlinked,
        "agents_files": files,
        "tree_paths": [e["path"] for e in entries if e["type"] == "blob"],
    }


def eligibility(snap: dict) -> list[str]:
    """Reasons a snapshot is ineligible (empty list = eligible)."""
    reasons = []
    if snap["license"] not in PERMISSIVE:
        reasons.append(f"license {snap['license']!r} not an open-source licence recognised by GitHub")
    if snap["fork"] or snap["archived"]:
        reasons.append("fork or archived")
    if snap["tree_truncated"]:
        reasons.append("git tree truncated")
    if snap["symlinked_agents_md"]:
        reasons.append("symlinked AGENTS.md present")
    nonempty = {f["path"]: sum(1 for ln in f["content"].splitlines() if ln.strip()) for f in snap["agents_files"]}
    if nonempty.get("AGENTS.md", 0) < MIN_NONEMPTY_LINES:
        reasons.append("root AGENTS.md missing or shorter than 5 non-empty lines")
    if not any("/" in p and n >= MIN_NONEMPTY_LINES for p, n in nonempty.items()):
        reasons.append("no nested AGENTS.md with at least 5 non-empty lines")
    return reasons


def save(snap: dict) -> Path:
    name = snap["repo"].replace("/", "__")
    out = SNAP_DIR / f"{name}.json"
    tree_paths = snap.pop("tree_paths")
    tp_file = SNAP_DIR / f"{name}.tree.json.gz"
    with gzip.open(tp_file, "wt", encoding="utf-8") as fh:
        json.dump(tree_paths, fh)
    snap["tree_paths_file"] = tp_file.name
    snap["tree_paths_count"] = len(tree_paths)
    out.write_text(json.dumps(snap, indent=1, ensure_ascii=False), encoding="utf-8")
    return out


def load(repo: str) -> tuple[dict, list[str]]:
    name = repo.replace("/", "__")
    snap = json.loads((SNAP_DIR / f"{name}.json").read_text(encoding="utf-8"))
    with gzip.open(SNAP_DIR / snap["tree_paths_file"], "rt", encoding="utf-8") as fh:
        tree_paths = json.load(fh)
    return snap, tree_paths


def verify(snap: dict) -> list[str]:
    """Provenance validation: recompute content hashes of every stored file."""
    errs = []
    for f in snap["agents_files"]:
        if sha256_bytes(f["content"].encode("utf-8")) != f["sha256"]:
            errs.append(f"{snap['repo']}:{f['path']} sha256 mismatch (non-UTF-8 bytes or edited content)")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-repos", type=int, default=40, help="frame positions to try, in seeded order")
    args = ap.parse_args()
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    log = {"seed": SEED, "frame_size": len(frame), "discovery_sha256": DISCOVERY_SHA256, "tried": []}
    for pos, repo in enumerate(frame[: args.max_repos]):
        try:
            snap = snapshot(repo)
        except Exception as exc:  # recorded, never retried silently
            log["tried"].append({"position": pos, "repo": repo, "status": "retrieval_error", "reasons": [str(exc)]})
            continue
        reasons = eligibility(snap)
        entry = {"position": pos, "repo": repo, "commit": snap["commit"], "license": snap["license"],
                 "agents_files": len(snap["agents_files"]), "status": "eligible" if not reasons else "ineligible",
                 "reasons": reasons}
        save(snap)
        log["tried"].append(entry)
        print(pos, repo, entry["status"], reasons, flush=True)
    log["retrieved_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT / "data" / "acquisition_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
