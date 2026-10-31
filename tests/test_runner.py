from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llm_eval_bench.result import RunResult
from llm_eval_bench.runner import _call_model, _resolve_model, run_suite
from llm_eval_bench.schema import EvalSuite, TestCase


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_suite(**kwargs) -> EvalSuite:
    defaults = dict(
        name="test-suite",
        default_model=None,
        cases=[
            TestCase(id="c1", prompt="Hello", expected_behaviour="Greet back"),
        ],
    )
    defaults.update(kwargs)
    return EvalSuite(**defaults)


def _make_case(**kwargs) -> TestCase:
    defaults = dict(id="c1", prompt="Hello", expected_behaviour="Greet back")
    defaults.update(kwargs)
    return TestCase(**defaults)


# ---------------------------------------------------------------------------
# _resolve_model
# ---------------------------------------------------------------------------

def test_resolve_model_override():
    case = _make_case(model="gpt-3.5-turbo")
    suite = _make_suite(default_model="gpt-4")
    assert _resolve_model(case, suite, override="gpt-4o-mini") == "gpt-4o-mini"


def test_resolve_model_case_wins_over_default():
    case = _make_case(model="gpt-3.5-turbo")
    suite = _make_suite(default_model="gpt-4")
    assert _resolve_model(case, suite, override=None) == "gpt-3.5-turbo"


def test_resolve_model_raises_if_none():
    case = _make_case(model=None)
    suite = _make_suite(default_model=None)
    with pytest.raises(ValueError, match="No model specified"):
        _resolve_model(case, suite, override=None)


# ---------------------------------------------------------------------------
# _call_model routing
# ---------------------------------------------------------------------------

def test_call_model_uses_anthropic_for_claude():
    mock_text = MagicMock()
    mock_text.text = "hello from claude"
    mock_message = MagicMock()
    mock_message.content = [mock_text]

    with patch("llm_eval_bench.runner.anthropic.Anthropic") as mock_anthropic_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_message
        mock_anthropic_cls.return_value = mock_client

        result = _call_model("Hi", "claude-3-haiku-20240307", None, None)

    assert result == "hello from claude"
    mock_anthropic_cls.assert_called_once()
    mock_client.messages.create.assert_called_once()


def test_call_model_uses_openai_for_gpt():
    mock_choice = MagicMock()
    mock_choice.message.content = "hello from gpt"
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    with patch("llm_eval_bench.runner.openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_openai_cls.return_value = mock_client

        result = _call_model("Hi", "gpt-4o-mini", None, None)

    assert result == "hello from gpt"
    mock_openai_cls.assert_called_once()
    mock_client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# run_suite end-to-end with mocks
# ---------------------------------------------------------------------------

def test_run_suite_saves_json(tmp_path):
    suite = _make_suite(default_model="gpt-4o-mini")

    with (
        patch("llm_eval_bench.runner._call_model", return_value="mocked response"),
        patch("llm_eval_bench.runner.judge_response", return_value=(0.9, "looks good")),
        patch("llm_eval_bench.runner.save_run") as mock_save,
    ):
        # Make save_run actually write a file so we can verify it
        real_results_dir = tmp_path / "results"

        def fake_save(run: RunResult, results_dir=None):
            real_results_dir.mkdir(parents=True, exist_ok=True)
            path = real_results_dir / f"{run.run_id}.json"
            path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
            return path

        mock_save.side_effect = fake_save

        run_result = run_suite(suite, "examples/factuality.yaml")

    # A file was written
    files = list(real_results_dir.glob("*.json"))
    assert len(files) == 1

    # The file is valid JSON and parses as RunResult
    loaded = RunResult.model_validate_json(files[0].read_text())
    assert loaded.suite_name == "test-suite"
    assert len(loaded.cases) == 1
    assert loaded.cases[0].score == 0.9
    assert loaded.cases[0].passed is True
