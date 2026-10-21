"""Frozen instruction-loading profile P1 (root and nested AGENTS.md, directory precedence).

This is an experimental interpretation grounded in https://agents.md/ ("the closest AGENTS.md to the edited file wins"),
not a claim that every coding tool implements the same loader. Everything here is deterministic.
"""

from __future__ import annotations

from posixpath import dirname

PROFILE_ID = "P1-agentsmd-directory-precedence-v1"

PROFILE_TEXT = """\
Instruction-loading profile P1 (frozen for this study)
1. Only files named AGENTS.md participate. README, CONTRIBUTING, CLAUDE.md, SKILL.md and user-level files are not loaded.
2. For a task that edits one target file, the binding loaded set is every AGENTS.md in the target's directory or in
   one of its ancestor directories up to the repository root (its ancestor chain). An AGENTS.md in an unrelated
   branch of the tree is not loaded for that target.
3. Every instruction in the loaded set is in force unless its own wording limits it (for example a condition such as
   "when editing docs" or "for Python code") and the task or target falls outside that limit.
4. When two loaded instructions impose incompatible requirements on the same decision, the instruction in the more
   deeply nested AGENTS.md (closer to the target) takes precedence over the ancestor instruction. Ancestor instructions
   about other decisions remain in force.
5. Instructions with equal authority (the same file, or files at the same depth) are not ranked by their order of
   appearance. An explicit statement in the files themselves can establish priority (for example "this file overrides
   the root guidelines" or "unless a package README says otherwise").
6. Explicit user prompts, cross-format files, imports, symbolic links and multiple working roots are outside scope.
"""


def file_dir(path: str) -> str:
    """Directory of a repository-relative POSIX path ('' for the root)."""
    d = dirname(path)
    return "" if d in ("", ".") else d


def is_ancestor_dir(anc: str, d: str) -> bool:
    """True if directory `anc` is `d` or one of its ancestors ('' is the root)."""
    if anc == "":
        return True
    return d == anc or d.startswith(anc + "/")


def depth(d: str) -> int:
    return 0 if d == "" else d.count("/") + 1


def loaded_set(target_path: str, agents_paths: list[str]) -> list[str]:
    """AGENTS.md files on the target's ancestor chain, ordered from root to nearest."""
    tdir = file_dir(target_path)
    chain = [p for p in agents_paths if is_ancestor_dir(file_dir(p), tdir)]
    return sorted(chain, key=lambda p: depth(file_dir(p)))


def relation(path_a: str, path_b: str) -> str:
    """Structural relation between two AGENTS.md files: same_file, ancestor_descendant, or unrelated."""
    if path_a == path_b:
        return "same_file"
    da, db = file_dir(path_a), file_dir(path_b)
    if is_ancestor_dir(da, db) or is_ancestor_dir(db, da):
        return "ancestor_descendant"
    return "unrelated"


def path_status(target_path: str, rule_path: str, agents_paths: list[str]) -> str:
    """'loaded' if the rule's file is on the target's ancestor chain, otherwise 'not_loaded'."""
    return "loaded" if rule_path in loaded_set(target_path, agents_paths + [rule_path]) else "not_loaded"


def structural_winner(target_path: str, path_a: str, path_b: str) -> str | None:
    """Which rule the profile's depth rule would favour if both are loaded and incompatible.

    Returns 'a', 'b', or None (equal authority, or at least one file not loaded)."""
    tdir = file_dir(target_path)
    da, db = file_dir(path_a), file_dir(path_b)
    if not (is_ancestor_dir(da, tdir) and is_ancestor_dir(db, tdir)):
        return None
    if depth(da) == depth(db):
        return None
    return "a" if depth(da) > depth(db) else "b"
