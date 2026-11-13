---
name: test-design-csv
description: "Use when deriving exhaustive test cases from an SRS or requirement document and writing them to a CSV file: positive, negative, boundary and edge cases, state transitions, decision tables, traceability to requirement IDs and blocking on open questions. Triggers: test design, test cases csv, test case generation, equivalence partitioning, boundary value analysis, decision table, state transition test, traceability matrix."
argument-hint: "[SRS path, default docs/SmartDrive_IVI_Specification_1_Bluetooth_Connectivity.md] [output CSV, default docs/test-cases.csv]"
---

# Test design to CSV

Turns a requirement document into a traceable CSV test-case set. Input is the SRS; output is one CSV file. Requirement review and owner feedback must come first (see `AGENTS.md` workflow order). The owner decisions in SRS section 14 are the confirmed baseline.

## When to use
- SRS review is done (or the user accepts the current baseline) and test cases are needed.
- Regenerating test cases after SRS changes (the CSV is overwritten).

## Rules
- Read only the SRS sections needed: section 5 (FR), 6 (NFR), 6.1 (CAPL docs), 7 (states), 8 (use cases), 9 (techniques), 10 (OQ), 14 (owner decisions).
- Section 14 decisions (Q-01..Q-51) add detail to the SRS text, for example the 6-digit passkey (Q-03), capacity checked at device selection (Q-09) and the extra transitions (Q-44). Use them as expected results and cite the Q-ID in `notes`.
- Never assume answers to OQ-01..OQ-08. Section 14 lists the questions that stay open (Q-07, Q-08, Q-10, Q-14, Q-15, Q-25, Q-28, Q-29), and Q-33 depends on OQ-06. Tests that depend on any of them get `status = Blocked` and list the OQ ID in `oq_dependency`.
- A "Workshop clarification point" that is neither decided in section 14 nor mapped to an OQ has no defined expected result: do not invent one; report it in the final summary.
- Every row traces to exactly one primary requirement ID (FR-BT-xxx or NFR-BT-xxx; DOC-CAPL-xxx for CAPL documentation tests).
- Synthetic data only: no real device IDs, passkeys or personal data. Use placeholders such as `DEV-001` and 6-digit passkeys: `123456` (valid) and `000000` (invalid).
- Do not edit the SRS.

## Procedure
1. Inventory requirements. List every FR-BT-001..008, NFR-BT-001..005 and DOC-CAPL-001..003. For each acceptance criterion bullet and each section 14 decision, record one testable condition.
2. Identify open questions. Map each OQ-01..08, each open section 14 question and each undecided "Workshop clarification point" to the conditions it affects.
3. Apply techniques per requirement:

| Technique | Apply to |
|-----------|----------|.9 s, 30.0 s (accepted, Q-22), 30.1 s; passkey length 5, 6, 7 digits; duplicate device IDs at 1 and 2 entries |
| Decision table | Pairing outcome from Bluetooth state x device availability x passkey validity x capacity (capacity is checked before the passkey step, Q-09)unavailable, removed), Bluetooth state (on, off) |
| Boundary value analysis | Paired-device count 0, 1, 4, 5, 6; timeout 29 s, 30 s, 31 s; passkey length at min and max; duplicate device IDs at 1 and 2 entries |
| Decision table | Pairing outcome from Bluetooth state x device availability x passkey validity x capacity |
| State transition | Not discovered, Discovered, Pairing, Paired, Connecting, Connected, Disconnected, Pairing failed, Removed. Cover every transition in SRS 7.1 and every invalid transition as negative |
| Use case | UC-BT-001 and UC-BT-002 maifrom input event to status change (Q-34, Q-35), list unchanged after failed scan, pairing or connection (NFR-BT-003, Q-38), displayed state equals simulator state (NFR-BT-004, Q-39), test hooks exist (NFR-BT-005, Q-40
| Error guessing | Repeated pairing, device disappears during pairing, restart during reconnection, Bluetooth off during call, cancel before timeout |
| NFR checks | Response time within 2 s (excluding external device), list not corrupted after failed scan or pairing (NFR-BT-003), displayed state equals simulator state (NFR-BT-004), test hooks exist (NFR-BT-005) |

4. Classify each case with exactly one `test_type`: Positive, Negative, Boundary, Edge, State, Decision, UseCase, NFR, Doc.
5. Write the minimum set per requirement: at least one Positive and one Negative. Add Boundary and Edge for every numeric limit, state or timing rule. Add State and Decision cases where the requirement has states or multiple conditions. Remove duplicates, but never drop a condition from the acceptance criteria.
6. Start from [test-case-template.csv](./assets/test-case-template.csv): keep its header, replace the example row, and add one row per test case. Column names, enums and ID patterns come from [test-case.schema.json](./assets/test-case.schema.json); do not hand-maintain them.
7. Run `python3 .github/skills/test-design-csv/scripts/validate_test_csv.py <csv>` and fix every reported issue. Rerun until exit code is 0.
8. Report: counts by requirement and by `test_type`, count of Blocked rows with their OQ IDs, and the file path. Do not create additional markdown reports.

## CSV format
- Columns, enums and ID patterns: [test-case.schema.json](./assets/test-case.schema.json). Column order is the `required` array.
- Example row and header: [test-case-template followed by `: `. `steps` are numbered from `1.`se-template.csv).
- `test_id` is `TC-BT-NNN-NN` (FR), `TC-NFR-NNN-NN` (NFR) or `TC-DOC-NNN-NN` (CAPL docs); NNN equals the requirement number.
- `test_title` starts with the requirement ID. `steps` are numbered and separated by `; `.
- `oq_dependency` is `none` or OQ IDs separated by `;`. `status` is `Blocked` if and only if an OQ is listed.
- Quote any field containing a comma, quote or newline. UTF-8, LF line endings, no blank rows.

## Coverage rules (enforced by the validator)
- Every requirement ID in the schema has at least one test case.
- Every FR has at least one Positive and one Negative case.
- Boundary cases exist for FR-BT-003 (device count 4/5/6) and FR-BT-007 (timeout around 30 s), as listed in `x-coverage`.
- `test_title` starts with the row's own `requirement_id`; `steps` start with `1.`.

Manual review still required: every acceptance-criteria bullet in SRS section 5 is covered, every section 14 decision has a row, every transition in SRS 7.1 (plus the Q-44 additions)

Manual review still required: every acceptance-criteria bullet in SRS section 5 is covered, every transition in SRS 7.1 has a row, and at least one invalid transition has a Negative row.

## Output
Default path: `docs/test-cases.csv`. Use the path given in the arguments if provided.
