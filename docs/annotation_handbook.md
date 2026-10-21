# CIPHER annotation handbook (v1.0, frozen 2026-10-21)

You judge one case at a time. A case contains a concrete task that edits one target file, a repository revision, the
instruction-loading profile P1, and two instructions quoted verbatim from AGENTS.md files (with their file paths, line
numbers, headings, surrounding section and any scope or precedence statements found in the loaded files).

Judge only from the evidence shown. Do not look up the repository, do not use model output, and do not discuss cases with
the other annotator until both of you have exported your final file. Some cases contain researcher-constructed variations
of real files; label every case exactly as presented.

## Profile P1 (summary; the full text is shown in every case)

1. Only AGENTS.md files count.
2. The binding loaded set for the target is every AGENTS.md in the target's directory or an ancestor directory.
   AGENTS.md files elsewhere in the tree are not loaded for this target.
3. A loaded instruction is in force unless its own wording limits it (a condition such as "for Python code" or "when
   editing docs") and the task or target falls outside that limit.
4. If two loaded instructions impose incompatible requirements on the same decision, the more deeply nested file (closer
   to the target) wins. Ancestor instructions about other decisions stay in force.
5. Equal authority (same file, or same depth) is not resolved by order of appearance. Explicit priority statements in
   the files can establish a winner.

## Decision sequence

Answer these in order. Stop at the first step that determines the label.

1. **Evidence sufficiency.** Can you tell what each instruction requires and whether it applies? If a decisive fact is
   missing or an instruction is too vague to interpret (for example "follow the usual conventions" with no further
   content), choose **Insufficient evidence**.
2. **Initial joint applicability (before any priority).** Is each instruction in the loaded set for this target, and
   does its own condition cover this task and target? If at least one is not active, choose **Disjoint
   applicability**. Being outranked by a more specific file is *not* inactivity; that is decided in step 4.
3. **Same decision, incompatible requirements.** Do the two active instructions regulate the same decision in ways that
   cannot both be satisfied while doing this task? If they can be satisfied together (different decisions, a
   preference next to a requirement, one rule refining the other, duplicates), choose **Compatible**.
4. **Priority.** If they are incompatible: does P1 or an explicit statement in the files make one of them win? If yes,
   choose **Valid override**. If no (same file, same depth, no explicit priority), choose **Unresolved conflict**.

## Labels

| Label | Use when |
|---|---|
| Unresolved conflict | Both hard requirements are in force for the same decision, cannot both be satisfied, and nothing in P1 or the files picks a winner. |
| Valid override | Both apply before priority, they are incompatible, and P1 (deeper file) or an explicit statement resolves which one wins. |
| Disjoint applicability | Before priority, at least one instruction is inactive for this target or task (not in the loaded set, or excluded by its own condition). |
| Compatible | Everything in force can be satisfied together: different decisions, refinements, duplicates, or a non-binding preference next to a requirement. |
| Insufficient evidence | The material shown cannot establish meaning, applicability, or precedence well enough to choose another label. |

## Reading instructions carefully

- Preserve modality. "Prefer X" is not "never use Y". "Use tool A" does not by itself forbid tool B.
- Examples, code blocks and descriptions of how the project works are not automatically rules. Treat them as binding only
  if the wording makes them requirements.
- An instruction that limits itself ("for documentation-only edits", "in tests") is inactive outside that limit
  (Disjoint). An instruction that is merely outranked by a deeper file is still active (Override or Compatible).
- A task can involve several decisions. Ask whether the two instructions constrain the same one.
- Use the "missing context" flag if you think the packet left out something decisive. Still choose your best label.

## What to record

Label (required); whether each instruction is active for this target and task; whether they regulate the same decision;
the winner if any; the evidence lines you relied on (path:line); a one- or two-sentence reason (required); confidence;
and the missing-context flag. Do not change a submitted judgment after you have seen the other annotator's answers.

## Workflow

1. Calibration packet (authored practice items show the handbook answer after you save; real calibration items do not).
2. Discuss calibration disagreements with the team. The handbook is frozen after this step; changes are logged.
3. Evaluation packet: label independently, export JSON, send the file to the coordinator.
4. The adjudicator reviews only cases where the two labels differ, sees both judgments and reasons, and records a final
   label with a reason. Initial judgments are preserved.
