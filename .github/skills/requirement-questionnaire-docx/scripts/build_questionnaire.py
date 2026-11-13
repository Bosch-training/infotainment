#!/usr/bin/env python3
"""Build and verify the requirement-review questionnaire (.docx) from a JSON file.

Usage: build_questionnaire.py INPUT.json OUTPUT.docx [--require REQ ...] [--oq OQ ...]
Exit code 0 = built and verified; 1 = input or verification failure (nothing is left half-valid).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

PRIORITIES = ("High", "Medium", "Low")
CATEGORIES = (
    "Ambiguity", "Missing info", "Inconsistency", "Untestable",
    "Incomplete states/transitions", "Boundary and negative gaps",
    "Open question", "NFR measurability",
)
DEFAULT_REQS = [f"FR-BT-{i:03d}" for i in range(1, 9)] + [f"NFR-BT-{i:03d}" for i in range(1, 6)]
DEFAULT_OQS = [f"OQ-{i:02d}" for i in range(1, 9)]
Q_FIELDS = ("id", "priority", "requirement", "srs_ref", "category", "excerpt",
            "question", "options", "why", "blocks")
EMPTY_ROWS = ("Owner response", "Decision / requirement change", "Answered by / date")
LABEL_FILL = "D9E2F3"


def fail(errors):
    print("INPUT/VERIFICATION FAILED:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)


def validate(data, reqs, oqs):
    errors = []
    meta = data.get("meta", {})
    for k in ("title", "srs_file", "srs_version", "review_date", "reviewer", "instructions"):
        if not meta.get(k):
            errors.append(f"meta.{k} missing")
    questions = data.get("questions", [])
    ids = [q.get("id") for q in questions]
    for dup, n in Counter(ids).items():
        if n > 1:
            errors.append(f"duplicate question id {dup}")
    seen_text = {}
    for q in questions:
        qid = q.get("id", "?")
        for f in Q_FIELDS:
            if not q.get(f):
                errors.append(f"{qid}: field '{f}' missing or empty")
        if q.get("priority") not in PRIORITIES:
            errors.append(f"{qid}: priority must be one of {PRIORITIES}")
        if q.get("category") not in CATEGORIES:
            errors.append(f"{qid}: category must be one of {CATEGORIES}")
        if not isinstance(q.get("options", []), list):
            errors.append(f"{qid}: options must be a list")
        key = re.sub(r"\W+", " ", q.get("question", "").lower()).strip()
        if key in seen_text:
            errors.append(f"{qid}: duplicates {seen_text[key]}")
        seen_text[key] = qid
        for f in ("owner_response", "decision", "answered_by"):
            if q.get(f):
                errors.append(f"{qid}: owner field '{f}' must be empty")
    cov = {c.get("req"): c for c in data.get("coverage", [])}
    for r in reqs:
        c = cov.get(r)
        if not c:
            errors.append(f"coverage missing {r}")
        elif c.get("testable") not in ("Yes", "Partly", "No"):
            errors.append(f"coverage {r}: testable must be Yes/Partly/No")
    oq_rows = {o.get("oq"): o for o in data.get("open_questions", [])}
    for o in oqs:
        row = oq_rows.get(o)
        if not row:
            errors.append(f"open_questions missing {o}")
        elif row.get("status") != "Unresolved":
            errors.append(f"{o}: status must be 'Unresolved'")
        elif not row.get("linked_q"):
            errors.append(f"{o}: linked_q missing")
    for o in oq_rows.values():
        for qid in re.findall(r"Q-\d+", o.get("linked_q", "")):
            if qid not in ids:
                errors.append(f"{o.get('oq')}: linked {qid} does not exist")
    if not data.get("next_step"):
        errors.append("next_step missing")
    return errors


def shade(cell, fill=LABEL_FILL):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def no_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(OxmlElement("w:cantSplit"))


def keep_next(cell):
    for p in cell.paragraphs:
        p.paragraph_format.keep_with_next = True


def set_text(cell, text, bold=False):
    cell.text = ""
    lines = text.split("\n") if isinstance(text, str) else [str(text)]
    p = cell.paragraphs[0]
    for i, line in enumerate(lines):
        if i:
            p = cell.add_paragraph()
        run = p.add_run(line)
        run.bold = bold


def kv_table(doc, rows, keep_together=False):
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    for label, value in rows:
        r = t.add_row()
        set_text(r.cells[0], label, bold=True)
        shade(r.cells[0])
        set_text(r.cells[1], value)
        r.cells[0].width = Pt(130)
        r.cells[1].width = Pt(340)
        if keep_together:
            no_split(r)
            keep_next(r.cells[0])
            keep_next(r.cells[1])
    return t


def grid_table(doc, header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, h in enumerate(header):
        set_text(t.rows[0].cells[i], h, bold=True)
        shade(t.rows[0].cells[i])
    for row in rows:
        r = t.add_row()
        for i, v in enumerate(row):
            set_text(r.cells[i], str(v))
    return t


def group_of(req):
    first = re.split(r"[,\s;/]+", req.strip())[0].upper()
    if first.startswith("NFR"):
        return 1
    if first.startswith("FR"):
        return 0
    return 2


def sort_key(q):
    first = re.split(r"[,\s;/]+", q["requirement"].strip())[0]
    return (group_of(q["requirement"]), first, q["id"])


def build(data, out_path):
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10)
    meta = data["meta"]

    doc.add_heading(meta["title"], level=0)
    kv_table(doc, [
        ("SRS file", meta["srs_file"]),
        ("SRS version", meta["srs_version"]),
        ("Review date", meta["review_date"]),
        ("Reviewer", meta["reviewer"]),
        ("How to answer", meta["instructions"]),
    ])

    questions = sorted(data["questions"], key=sort_key)

    doc.add_heading("Summary", level=1)
    by_p = Counter(q["priority"] for q in questions)
    by_c = Counter(q["category"] for q in questions)
    grid_table(doc, ["Priority", "Questions"],
               [(p, by_p.get(p, 0)) for p in PRIORITIES] + [("Total", len(questions))])
    doc.add_paragraph()
    grid_table(doc, ["Category", "Questions"],
               [(c, by_c[c]) for c in CATEGORIES if by_c.get(c)])

    doc.add_heading("Questions", level=1)
    group_names = ("Functional requirements", "Non-functional requirements", "Cross-cutting")
    cur_group, cur_req = None, None
    for q in questions:
        g = group_of(q["requirement"])
        if g != cur_group:
            doc.add_heading(group_names[g], level=2)
            cur_group, cur_req = g, None
        first = re.split(r"[,\s;/]+", q["requirement"].strip())[0]
        if first != cur_req:
            p = doc.add_paragraph()
            p.add_run(first).bold = True
            p.paragraph_format.keep_with_next = True
            cur_req = first
        opts = "\n".join(q["options"])
        kv_table(doc, [
            ("Q-ID / Priority", f"{q['id']} | {q['priority']}"),
            ("Requirement", q["requirement"]),
            ("SRS reference", q["srs_ref"]),
            ("Category", q["category"]),
            ("SRS excerpt", f"\u201c{q['excerpt']}\u201d"),
            ("Question", q["question"]),
            ("Options / Proposed (unconfirmed)", opts),
            ("Why it matters", q["why"]),
            ("Blocks", q["blocks"]),
            (EMPTY_ROWS[0], ""),
            (EMPTY_ROWS[1], ""),
            ("Status", "Open"),
            (EMPTY_ROWS[2], ""),
        ], keep_together=True)
        doc.add_paragraph()

    doc.add_heading("Appendix A \u2013 Open questions OQ-01..OQ-08", level=1)
    grid_table(
        doc,
        ["OQ", "Related Req", "Status", "Testable value needed", "Blocked test areas", "Linked Q-ID"],
        [(o["oq"], o["related"], o["status"], o["value_needed"], o["blocked"], o["linked_q"])
         for o in data["open_questions"]],
    )

    doc.add_heading("Appendix B \u2013 Coverage", level=1)
    grid_table(
        doc,
        ["Req ID", "Reviewed", "Questions", "Testable as written"],
        [(c["req"], c.get("reviewed", "Yes"), c.get("questions", "-"), c["testable"])
         for c in data["coverage"]],
    )

    doc.add_heading("Appendix C \u2013 Clear requirements", level=1)
    clear = data.get("clear") or ["None identified."]
    for item in clear:
        doc.add_paragraph(item, style="List Bullet")

    doc.add_heading("Next step", level=1)
    doc.add_paragraph(data["next_step"])

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)


def verify(data, out_path, oqs):
    errors = []
    p = Path(out_path)
    if not p.exists() or p.stat().st_size == 0:
        return [f"{out_path} missing or empty"]
    doc = Document(str(p))
    text = "\n".join(par.text for par in doc.paragraphs)
    cell_text = "\n".join(c.text for t in doc.tables for r in t.rows for c in r.cells)
    q_tables = [t for t in doc.tables
                if t.rows and t.rows[0].cells[0].text == "Q-ID / Priority"]
    if len(q_tables) != len(data["questions"]):
        errors.append(f"question tables {len(q_tables)} != questions {len(data['questions'])}")
    for t in q_tables:
        vals = {r.cells[0].text: r.cells[1].text for r in t.rows}
        for label in EMPTY_ROWS:
            if vals.get(label):
                errors.append(f"{vals['Q-ID / Priority']}: '{label}' not empty")
        if vals.get("Status") != "Open":
            errors.append(f"{vals['Q-ID / Priority']}: status not Open")
    for o in oqs:
        if o not in cell_text:
            errors.append(f"{o} not found in document")
    for h in ("Summary", "Questions", "Next step"):
        if h not in text:
            errors.append(f"heading '{h}' missing")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--require", nargs="*", default=DEFAULT_REQS, help="Req IDs that must appear in coverage")
    ap.add_argument("--oq", nargs="*", default=DEFAULT_OQS, help="OQ IDs that must be listed as Unresolved")
    a = ap.parse_args()

    data = json.loads(Path(a.input).read_text(encoding="utf-8"))
    errs = validate(data, a.require, a.oq)
    if errs:
        fail(errs)
    build(data, a.output)
    errs = verify(data, a.output, a.oq)
    if errs:
        fail(errs)

    qs = data["questions"]
    by_p = Counter(q["priority"] for q in qs)
    print(f"OK {a.output}: {len(qs)} questions "
          f"(High {by_p.get('High', 0)}, Medium {by_p.get('Medium', 0)}, Low {by_p.get('Low', 0)}); "
          f"{len(data['open_questions'])} OQ rows; {len(data['coverage'])} coverage rows")


if __name__ == "__main__":
    main()
