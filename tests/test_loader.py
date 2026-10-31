from pathlib import Path

import pytest
from pydantic import ValidationError

from llm_eval_bench.loader import load_suite
from llm_eval_bench.schema import TestCase

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def test_load_factuality_suite():
    suite = load_suite(EXAMPLES_DIR / "factuality.yaml")
    assert suite.name
    assert len(suite.cases) == 5


@pytest.mark.parametrize(
    "filename",
    ["factuality.yaml", "instruction_following.yaml", "code_quality.yaml"],
)
def test_load_all_bundled_suites(filename):
    suite = load_suite(EXAMPLES_DIR / filename)
    assert len(suite.cases) > 0


def test_default_tags_empty(tmp_path):
    yaml_text = """\
name: Test Suite
cases:
  - id: tc-001
    prompt: Hello?
    expected_behaviour: Respond with a greeting.
"""
    f = tmp_path / "suite.yaml"
    f.write_text(yaml_text)
    suite = load_suite(f)
    assert suite.cases[0].tags == []


def test_model_override_none_by_default(tmp_path):
    yaml_text = """\
name: Test Suite
cases:
  - id: tc-001
    prompt: Hello?
    expected_behaviour: Respond with a greeting.
"""
    f = tmp_path / "suite.yaml"
    f.write_text(yaml_text)
    suite = load_suite(f)
    assert suite.cases[0].model is None


def test_missing_required_field_raises(tmp_path):
    yaml_text = """\
name: Bad Suite
cases:
  - id: tc-001
    expected_behaviour: Should have a prompt but doesn't.
"""
    f = tmp_path / "bad.yaml"
    f.write_text(yaml_text)
    with pytest.raises(ValidationError):
        load_suite(f)


def test_duplicate_ids_raises(tmp_path):
    yaml_text = """\
name: Dupe Suite
cases:
  - id: dupe-id
    prompt: First case.
    expected_behaviour: Something.
  - id: dupe-id
    prompt: Second case with same id.
    expected_behaviour: Something else.
"""
    f = tmp_path / "dupes.yaml"
    f.write_text(yaml_text)
    with pytest.raises(ValueError, match="Duplicate test case ids"):
        load_suite(f)


def test_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_suite("does_not_exist.yaml")
