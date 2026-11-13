---
name: requirement-questionnaire-docx
description: "Use when generating the requirement-review clarification questionnaire as a Word (.docx) file from reviewed SRS findings: owner response fields, summary counts, OQ-01..OQ-08 appendix, coverage appendix, then self-verification. Triggers: create questionnaire docx, clarification questionnaire, requirement-review-questionnaire.docx, python-docx questionnaire."
argument-hint: "[output path, default docs/requirement-review-questionnaire.docx]"
---

# Requirement questionnaire (.docx)

Turns finished review findings into `docs/requirement-review-questionnaire.docx`. Finding the issues is the reviewer's job (see the `requirement-review` agent); this skill only formats, validates and verifies.

## When to use
- Review findings exist and must be delivered to the SRS owner as a Word questionnaire.
- Regenerating after fixing findings (the file is overwritten).

## Procedure
1. Copy the structure of [questionnaire-template.json](./assets/questionnaire-template.json) and fill it from the findings. Write it to a temp path outside the workspace (for example `/tmp/questionnaire.json`).
   - `questions[]`: `id`, `priority` (High/Medium/Low), `requirement`, `srs_ref`, `category`, `excerpt` (quoted SRS text), `question`, `options` (list; last is "Other: ____"; mark defaults "Proposed (unconfirmed)"), `why`, `blocks`.
   - Allowed categories: Ambiguity, Missing info, Inconsistency, Untestable, Incomplete states/transitions, Boundary and negative gaps, Open question, NFR measurability.
   - `open_questions[]`: one row per OQ-01..OQ-08, `status` always `Unresolved`, each with a `linked_q`.
   - `coverage[]`: one row per FR-BT-001..008 and NFR-BT-001..005, `testable` is Yes/Partly/No.
   - Never fill owner response, decision or answered-by fields.
2. Run the builder (it validates the input, builds, reopens and checks the file):
   ```bash
   python3 .github/skills/requirement-questionnaire-docx/scripts/build_questionnaire.py /tmp/questionnaire.json docs/requirement-review-questionnaire.docx
   ```
   Override required IDs for other SRSs with `--require REQ ...` and `--oq OQ ...`.
3. If it exits non-zero, fix the listed JSON errors and rerun. Do not edit the .docx by hand.
4. Delete the temp JSON. Report counts by priority, blocked requirements and the file path.

## What the builder produces (in order)
Title block, Summary (by priority and category), Questions grouped FR then NFR then cross-cutting (one table per question, kept on one page), Appendix A (OQ), Appendix B (coverage), Appendix C (clear requirements), Next step.

## Checks performed by the script
- Required fields present, valid priority and category, no duplicate Q-IDs or duplicate question text.
- Owner fields empty, Status `Open`.
- Every required requirement in coverage; every OQ listed as Unresolved with an existing linked Q-ID.
- File exists, is non-empty, reopens, question-table count matches input.

## Requirements
`python-docx` must be installed. If it is missing, ask before installing.
