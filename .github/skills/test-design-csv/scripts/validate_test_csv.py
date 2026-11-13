#!/usr/bin/env python3
"""Validate a test-case CSV against assets/test-case.schema.json and coverage rules.

Usage: validate_test_csv.py CSV_FILE
Exit code 0 = valid and covered; 1 = errors listed on stdout; 2 = usage error.
"""
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "assets" / "test-case.schema.json"
TEST_ID_PREFIX = {"FR-BT": "BT", "NFR-BT": "NFR", "DOC-CAPL": "DOC"}


def check_field(col, val, spec, line, errors):
    if len(val) < spec.get("minLength", 0):
        errors.append(f"line {line}: {col} is empty")
    if "enum" in spec and val not in spec["enum"]:
        errors.append(f"line {line}: {col}='{val}' not in allowed values")
    if "pattern" in spec and val and not re.fullmatch(spec["pattern"], val):
        errors.append(f"line {line}: {col}='{val}' does not match {spec['pattern']}")


def check_row(row, line, props, coverage, errors):
    for col, spec in props.items():
        check_field(col, row[col], spec, line, errors)

    if not row["test_title"].startswith(row["requirement_id"] + ": "):
        errors.append(f"line {line}: test_title must start with '{row['requirement_id']}: '")
    if not row["steps"].startswith("1."):
        errors.append(f"line {line}: steps must be numbered starting with '1.'")

    blocked = row["status"] == "Blocked"
    has_oq = row["oq_dependency"] != "none"
    if blocked != has_oq:
        errors.append(f"line {line}: status={row['status']} inconsistent with oq_dependency={row['oq_dependency']}")

    for oq in filter(None, row["oq_dependency"].split(";")):
        if oq != "none" and oq not in coverage["oq_ids"]:
            errors.append(f"line {line}: unknown OQ '{oq}'")

    req_parts = row["requirement_id"].rsplit("-", 1)
    req_prefix, req_num = req_parts[0], req_parts[1]
    expected_tc = TEST_ID_PREFIX.get(req_prefix)
    tc_parts = row["test_id"].split("-")
    if expected_tc is None or tc_parts[1] != expected_tc or tc_parts[2] != req_num:
        errors.append(f"line {line}: test_id '{row['test_id']}' does not match requirement '{row['requirement_id']}'")


def check_coverage(rows, props, coverage, errors):
    present = Counter(r["requirement_id"] for _, r in rows)
    for req in props["requirement_id"]["enum"]:
        if present[req] == 0:
            errors.append(f"coverage: {req} has no test case")

    types = defaultdict(set)
    for _, r in rows:
        types[r["requirement_id"]].add(r["test_type"])
    prefix = coverage["positive_negative_prefix"]
    for req in props["requirement_id"]["enum"]:
        if req.startswith(prefix):
            for needed in ("Positive", "Negative"):
                if needed not in types[req]:
                    errors.append(f"coverage: {req} has no {needed} test case")

    for req in coverage["boundary_required"]:
        if "Boundary" not in types[req]:
            errors.append(f"coverage: {req} has no Boundary test case")

    referenced = set()
    for _, r in rows:
        referenced.update(oq for oq in r["oq_dependency"].split(";") if oq != "none")
    for oq in coverage["oq_ids"]:
        if oq not in referenced:
            errors.append(f"coverage: {oq} is not referenced by any row")


def main(argv):
    if len(argv) != 2:
        print("usage: validate_test_csv.py CSV_FILE", file=sys.stderr)
        return 2

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    props = schema["properties"]
    columns = schema["required"]
    coverage = schema["x-coverage"]
    errors = []
    rows = []

    if not Path(argv[1]).is_file():
        print(f"usage error: {argv[1]} not found", file=sys.stderr)
        return 2

    with Path(argv[1]).open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        if header != columns:
            errors.append(f"header mismatch: expected {','.join(columns)}")
        for line, rec in enumerate(reader, start=2):
            if not any(c.strip() for c in rec):
                errors.append(f"line {line}: blank row")
                continue
            if len(rec) != len(columns):
                errors.append(f"line {line}: {len(rec)} fields, expected {len(columns)}")
                continue
            row = dict(zip(columns, rec))
            rows.append((line, row))
            check_row(row, line, props, coverage, errors)

    ids = Counter(r["test_id"] for _, r in rows)
    for tid, n in ids.items():
        if n > 1:
            errors.append(f"duplicate test_id {tid} ({n} rows)")

    check_coverage(rows, props, coverage, errors)

    if errors:
        print(f"FAILED: {len(errors)} issue(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    by_type = Counter(r["test_type"] for _, r in rows)
    blocked = Counter(r["oq_dependency"] for _, r in rows if r["status"] == "Blocked")
    print(f"OK: {len(rows)} test cases, all requirements covered")
    print("By type: " + ", ".join(f"{k}={v}" for k, v in sorted(by_type.items())))
    print(f"Ready: {sum(1 for _, r in rows if r['status'] == 'Ready')}, Blocked: {sum(blocked.values())}")
    for dep, n in sorted(blocked.items()):
        print(f"  Blocked by {dep}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
