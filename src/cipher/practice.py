"""Authored practice items for annotator calibration.

These are invented by the researchers to cover label boundaries. They are not research data, are never scored, and
show the handbook answer only after the annotator has saved a judgment.
"""

from __future__ import annotations

from .cases import packet
from .mdparse import split_lines

FOUR = "- Use exactly four spaces per indentation level."
TWO = "- Use exactly two spaces per indentation level."


def _rule(files: dict[str, str], path: str, needle: str) -> dict:
    lines = split_lines(files[path])
    i = next(n for n, ln in enumerate(lines, start=1) if needle in ln)
    head = next((ln.lstrip("# ").strip() for ln in reversed(lines[:i]) if ln.startswith("#")), "")
    return {"path": path, "start_line": i, "end_line": i, "heading": head, "text": lines[i - 1],
            "section_first_line": 1, "section_last_line": len(files[path].rstrip("\n").split("\n")),
            "section_text": files[path].rstrip("\n")}


def _item(pid: str, files: dict[str, str], target: str, task: str, r1: tuple[str, str], r2: tuple[str, str],
          answer: str, why: str) -> dict:
    agents = sorted(files)
    pk = packet(files, agents, target, _rule(files, *r1), _rule(files, *r2))
    return {"case_id": pid, "split": "practice", "stratum": "authored_practice", "repo": "example/webshop (authored)",
            "commit": "n/a", "task": task, "task_origin": "researcher-authored", "target_path": target,
            "packet": pk, "practice_answer": answer, "practice_explanation": why}


def practice_items() -> list[dict]:
    root = "# Webshop agent guide\n\n## Style\n" + FOUR + "\n- Prefer descriptive variable names.\n"
    return [
        _item("P1", {"AGENTS.md": root + "\n## Formatting\n" + TWO + "\n"}, "web/src/button.ts",
              "Add a new helper function to `web/src/button.ts`.", ("AGENTS.md", "four spaces"),
              ("AGENTS.md", "two spaces"), "Unresolved conflict",
              "Both rules are in the root file, both apply to the new code, they set different indentation for the "
              "same lines, and equal authority is not ranked by order of appearance."),
        _item("P2", {"AGENTS.md": root, "web/AGENTS.md": "# Web package\n\n## Style\n" + TWO + "\n"},
              "web/src/button.ts", "Add a new helper function to `web/src/button.ts`.", ("AGENTS.md", "four spaces"),
              ("web/AGENTS.md", "two spaces"), "Valid override",
              "Both files are on the target's ancestor chain, so both apply before priority. They are incompatible; "
              "web/AGENTS.md is deeper, so its two-space rule wins under P1."),
        _item("P3", {"AGENTS.md": root, "api/AGENTS.md": "# API package\n\n## Style\n" + TWO + "\n"},
              "web/src/button.ts", "Add a new helper function to `web/src/button.ts`.", ("AGENTS.md", "four spaces"),
              ("api/AGENTS.md", "two spaces"), "Disjoint applicability",
              "api/AGENTS.md is not on the ancestor chain of web/src/button.ts, so the two-space rule is not loaded "
              "for this target."),
        _item("P4", {"AGENTS.md": "# Webshop agent guide\n\n## Checks\n- Run `pnpm test` before committing.\n",
                     "web/AGENTS.md": "# Web package\n\n## Style\n" + TWO + "\n"},
              "web/src/button.ts", "Add a new helper function to `web/src/button.ts` and commit it.",
              ("AGENTS.md", "pnpm test"), ("web/AGENTS.md", "two spaces"), "Compatible",
              "Both apply, but they regulate different decisions (testing before a commit, indentation); both can be "
              "followed."),
        _item("P5", {"AGENTS.md": "# Webshop agent guide\n\n## Style\n- For Python code, use four spaces per "
                                  "indentation level.\n- Use two spaces per indentation level in YAML files.\n"},
              "config/app.yaml", "Add a new setting to `config/app.yaml`.", ("AGENTS.md", "For Python"),
              ("AGENTS.md", "YAML"), "Disjoint applicability",
              "The four-space rule limits itself to Python code; the target is a YAML file, so that rule is inactive "
              "before any priority question arises."),
        _item("P6", {"AGENTS.md": "# Webshop agent guide\n\n## Style\n- Follow the team's usual formatting "
                                  "conventions.\n", "web/AGENTS.md": "# Web package\n\n## Style\n" + TWO + "\n"},
              "web/src/button.ts", "Add a new helper function to `web/src/button.ts`.",
              ("AGENTS.md", "usual formatting"), ("web/AGENTS.md", "two spaces"), "Insufficient evidence",
              "The shown material never says what the usual conventions are, so it is impossible to tell whether "
              "they agree with the two-space rule."),
    ]
