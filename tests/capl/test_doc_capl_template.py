"""Checks on tests/capl/capl_script_template.can: SRS 6.1 DOC-CAPL-001..003 (supplement of NFR-BT-005)."""
import re
from pathlib import Path

import pytest

TEMPLATE = Path(__file__).with_name("capl_script_template.can")

C_KEYWORDS = {"if", "else", "for", "while", "do", "switch", "case", "return", "sizeof", "break", "continue"}
ACCEPTED_SOURCES = (
    "help.vector.com",
    "kb.vector.com",
    "vector.com application note",
    "offline capl function reference",
)
VERSION_PATTERN = re.compile(r"CANoe \d+ SP\d+")
HEADER_COMMENT = re.compile(r"/\*(?!@!).*?\*/", re.DOTALL)
NOISE = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"', re.DOTALL)
CITATION_LINE = re.compile(r"^[ \t]*\*[ \t]+(\w+)[ \t]*\|(.*)$", re.MULTILINE)
VERSION_FIELD = re.compile(r"^[ \t]*\*?[ \t]*CANoe version[ \t]*:[ \t]*(.*)$", re.MULTILINE)


def read_template() -> str:
    return TEMPLATE.read_text(encoding="utf-8")


def split_template(text: str) -> tuple[str, str]:
    header = HEADER_COMMENT.search(text)
    return header.group(0), text[header.end():]


def citations(text: str) -> list[tuple[str, list[str]]]:
    header, _ = split_template(text)
    return [
        (m.group(1), [f.strip() for f in (m.group(1) + "|" + m.group(2)).split("|")])
        for m in CITATION_LINE.finditer(header)
    ]


def called_functions(text: str) -> set[str]:
    _, code = split_template(text)
    code = NOISE.sub(" ", code)
    names = set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", code))
    return names - C_KEYWORDS


def uncited_calls(text: str) -> set[str]:
    return called_functions(text) - {name for name, _ in citations(text)}


def citation_format_problems(text: str) -> list[str]:
    problems = []
    for name, fields in citations(text):
        if len(fields) != 4 or not all(fields):
            problems.append(f"{name}: citation does not identify a Vector help or KB entry")
    return problems


def version_problems(text: str) -> list[str]:
    header, _ = split_template(text)
    values = [v.strip() for v in VERSION_FIELD.findall(header)]
    if not values:
        return ["header has no CANoe version"]
    return [
        f"no concrete CANoe version recorded: {v!r}"
        for v in values
        if not VERSION_PATTERN.fullmatch(v)
    ]


def is_accepted_source(source: str) -> bool:
    return any(token in source.lower() for token in ACCEPTED_SOURCES)


def source_problems(text: str) -> set[str]:
    accepted: dict[str, bool] = {}
    for name, fields in citations(text):
        accepted[name] = accepted.get(name, False) or is_accepted_source(fields[1])
    return {name for name, ok in accepted.items() if not ok}


def collapsed_header(text: str) -> str:
    header, _ = split_template(text)
    return re.sub(r"\s*\n[ \t]*\*[ \t]?", " ", header)


@pytest.fixture
def template_text() -> str:
    return read_template()


@pytest.fixture
def make_copy(tmp_path):
    def _make(text: str) -> str:
        path = tmp_path / "copy.can"
        path.write_text(text, encoding="utf-8")
        return path.read_text(encoding="utf-8")

    return _make


def replace_once(text: str, old: str, new: str) -> str:
    assert old in text
    return text.replace(old, new, 1)


def replace_citation(text: str, name: str, new_line: str) -> str:
    pattern = re.compile(rf"^[ \t]*\*[ \t]+{name}[ \t]*\|.*$", re.MULTILINE)
    assert pattern.search(text)
    return pattern.sub(f" *   {new_line}", text, count=1)


def add_citation(text: str, new_line: str) -> str:
    return replace_once(text, " */\n\nvariables", f" *   {new_line}\n */\n\nvariables")


@pytest.mark.doc
def test_doc_capl_001_01_every_called_builtin_has_citation(template_text):
    """TC-DOC-001-01 / DOC-CAPL-001"""
    called = called_functions(template_text)
    assert {"write", "setTimer"} <= called
    assert uncited_calls(template_text) == set()


@pytest.mark.negative
def test_doc_capl_001_02_uncited_builtin_call_flagged(template_text, make_copy):
    """TC-DOC-001-02 / DOC-CAPL-001"""
    original = read_template()
    copy = make_copy(replace_once(template_text, 'write("Script started");', 'write("Script started");\n  output(msg);'))
    assert uncited_calls(copy) == {"output"}
    assert read_template() == original


@pytest.mark.positive
def test_doc_capl_001_03_citation_lines_have_four_fields(template_text):
    """TC-DOC-001-03 / DOC-CAPL-001"""
    cited = dict(citations(template_text))
    assert {"write", "setTimer"} <= set(cited)
    for name in ("write", "setTimer"):
        assert len(cited[name]) == 4
        assert all(cited[name])
    assert citation_format_problems(template_text) == []


@pytest.mark.negative
def test_doc_capl_001_04_empty_entry_title_flagged(template_text, make_copy):
    """TC-DOC-001-04 / DOC-CAPL-001"""
    line = "write | CANoe offline CAPL function reference |  | CANoe 17 SP3"
    copy = make_copy(replace_citation(template_text, "write", line))
    problems = citation_format_problems(copy)
    assert len(problems) == 1
    assert problems[0].startswith("write:")


@pytest.mark.edge
def test_doc_capl_001_05_c_style_constructs_need_no_citation(template_text, make_copy):
    """TC-DOC-001-05 / DOC-CAPL-001"""
    constructs = (
        'write("Script started");\n'
        "  if (1) { }\n"
        "  for (i = 0; i < 1; i++) { }\n"
        "  while (0) { }\n"
        "  switch (1) { case 1: break; }"
    )
    copy = make_copy(replace_once(template_text, 'write("Script started");', constructs))
    assert uncited_calls(copy) == set()


@pytest.mark.edge
def test_doc_capl_001_06_name_in_string_or_comment_not_a_call(template_text, make_copy):
    """TC-DOC-001-06 / DOC-CAPL-001"""
    body = 'write("call output later");\n  // output(msg) is called later'
    copy = make_copy(replace_once(template_text, 'write("Step timer elapsed");', body))
    assert "output" not in called_functions(copy)
    assert uncited_calls(copy) == set()


@pytest.mark.positive
def test_doc_capl_001_07_header_has_citations_section(template_text):
    """TC-DOC-001-07 / DOC-CAPL-001"""
    header, _ = split_template(template_text)
    heading = next(line for line in header.splitlines() if "Citations" in line)
    for doc_id in ("DOC-CAPL-001", "DOC-CAPL-002", "DOC-CAPL-003"):
        assert doc_id in heading
    assert len(citations(template_text)) >= 1
    assert template_text.index("Citations") < template_text.index("variables")


@pytest.mark.positive
def test_doc_capl_002_01_header_records_canoe_17_sp3(template_text):
    """TC-DOC-002-01 / DOC-CAPL-002"""
    header, _ = split_template(template_text)
    assert [v.strip() for v in VERSION_FIELD.findall(header)] == ["CANoe 17 SP3"]


@pytest.mark.boundary
def test_doc_capl_002_02_version_matches_pattern(template_text):
    """TC-DOC-002-02 / DOC-CAPL-002"""
    header, _ = split_template(template_text)
    value = VERSION_FIELD.findall(header)[0].strip()
    assert VERSION_PATTERN.fullmatch(value)
    assert re.search(r"CANoe (\d+) SP", value).group(1)


@pytest.mark.negative
def test_doc_capl_002_03_missing_version_field_flagged(template_text, make_copy):
    """TC-DOC-002-03 / DOC-CAPL-002"""
    stripped = re.sub(r"^[ \t]*\*[ \t]*CANoe version[ \t]*:.*\n", "", template_text, flags=re.MULTILINE)
    assert stripped != template_text
    assert version_problems(make_copy(stripped)) == ["header has no CANoe version"]


@pytest.mark.negative
@pytest.mark.parametrize("value", ["", "<version>", "CANoe"])
def test_doc_capl_002_04_placeholder_or_empty_version_flagged(template_text, make_copy, value):
    """TC-DOC-002-04 / DOC-CAPL-002"""
    copy = make_copy(replace_once(template_text, "CANoe version:   CANoe 17 SP3", f"CANoe version:   {value}"))
    problems = version_problems(copy)
    assert len(problems) == 1
    assert problems[0].startswith("no concrete CANoe version recorded")


@pytest.mark.edge
def test_doc_capl_002_05_version_recorded_once_in_header(template_text):
    """TC-DOC-002-05 / DOC-CAPL-002"""
    header, _ = split_template(template_text)
    assert len(re.findall(r"CANoe version\s*:", template_text)) == 1
    assert len(re.findall(r"CANoe version\s*:", header)) == 1
    assert template_text.index("CANoe version") < template_text.index("variables")


@pytest.mark.positive
def test_doc_capl_002_06_citation_version_matches_header(template_text):
    """TC-DOC-002-06 / DOC-CAPL-002"""
    header, _ = split_template(template_text)
    header_version = VERSION_FIELD.findall(header)[0].strip()
    lines = citations(template_text)
    assert lines
    for _, fields in lines:
        assert VERSION_PATTERN.fullmatch(fields[-1])
        assert fields[-1] == header_version == "CANoe 17 SP3"


@pytest.mark.positive
def test_doc_capl_003_01_every_citation_uses_accepted_source(template_text):
    """TC-DOC-003-01 / DOC-CAPL-003"""
    cited = dict(citations(template_text))
    assert all(is_accepted_source(fields[1]) for _, fields in citations(template_text))
    for name in ("write", "setTimer"):
        assert "offline capl function reference" in cited[name][1].lower()


@pytest.mark.negative
def test_doc_capl_003_02_forum_only_source_flagged(template_text, make_copy):
    """TC-DOC-003-02 / DOC-CAPL-003"""
    line = "setTimer | Vector forum thread | Timer question | CANoe 17 SP3"
    copy = make_copy(replace_citation(template_text, "setTimer", line))
    assert source_problems(copy) == {"setTimer"}


@pytest.mark.negative
def test_doc_capl_003_03_blog_only_source_flagged(template_text, make_copy):
    """TC-DOC-003-03 / DOC-CAPL-003"""
    line = "write | CAPL tips blog | Printing from CAPL | CANoe 17 SP3"
    copy = make_copy(replace_citation(template_text, "write", line))
    assert source_problems(copy) == {"write"}


@pytest.mark.decision
def test_doc_capl_003_04_forum_plus_vector_source_accepted(template_text, make_copy):
    """TC-DOC-003-04 / DOC-CAPL-003"""
    copy = make_copy(add_citation(template_text, "write | Vector forum thread | Printing question | CANoe 17 SP3"))
    assert source_problems(copy) == set()


@pytest.mark.decision
def test_doc_capl_003_05_forum_plus_blog_without_vector_source_flagged(template_text, make_copy):
    """TC-DOC-003-05 / DOC-CAPL-003"""
    line = "setTimer | Vector forum thread | Timer question | CANoe 17 SP3"
    text = replace_citation(template_text, "setTimer", line)
    copy = make_copy(add_citation(text, "setTimer | CAPL tips blog | Timers in CAPL | CANoe 17 SP3"))
    assert source_problems(copy) == {"setTimer"}


@pytest.mark.negative
def test_doc_capl_003_06_source_outside_accepted_sources_flagged(template_text, make_copy):
    """TC-DOC-003-06 / DOC-CAPL-003"""
    line = "write | Third-party tutorial site | Write intro | CANoe 17 SP3"
    copy = make_copy(replace_citation(template_text, "write", line))
    assert source_problems(copy) == {"write"}


@pytest.mark.positive
def test_doc_capl_003_07_header_states_forum_blog_never_sole_source(template_text):
    """TC-DOC-003-07 / DOC-CAPL-003"""
    header = collapsed_header(template_text).lower()
    assert "a forum or blog is never the sole source" in header
    for source in ("help.vector.com", "kb.vector.com", "application note", "offline capl function reference"):
        assert source in header


@pytest.mark.doc
def test_nfr_bt_005_40_header_trace_field_names_nfr_bt_005(template_text):
    """TC-NFR-005-40 / NFR-BT-005"""
    header, _ = split_template(template_text)
    trace = re.search(r"^[ \t]*\*[ \t]*Trace[ \t]*:(.*)$", header, re.MULTILINE)
    assert trace
    assert "NFR-BT-005" in trace.group(1)


@pytest.mark.doc
def test_nfr_bt_005_41_header_oq_dependency_defaults_to_none(template_text):
    """TC-NFR-005-41 / NFR-BT-005"""
    header, _ = split_template(template_text)
    field = re.search(r"^[ \t]*\*[ \t]*OQ dependency[ \t]*:[ \t]*(\S+)(.*)$", header, re.MULTILINE)
    assert field
    assert field.group(1) == "none"
    assert "Blocked" in field.group(2)
    assert "linked to its question" in field.group(2)
