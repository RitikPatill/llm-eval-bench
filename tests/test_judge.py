from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from llm_eval_bench.judge import judge_response


def _mock_openai_response(content: str):
    """Build a minimal openai completion mock that returns `content`."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    return mock_completion


def _patch_openai(content: str):
    completion = _mock_openai_response(content)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = completion
    return patch("llm_eval_bench.judge.openai.OpenAI", return_value=mock_client)


def test_judge_parses_valid_json():
    payload = json.dumps({"score": 0.9, "rationale": "correct"})
    with _patch_openai(payload):
        score, rationale = judge_response(
            prompt="What is 2+2?",
            expected_behaviour="Returns 4",
            response="4",
        )
    assert score == 0.9
    assert rationale == "correct"


def test_judge_fallback_on_bad_json():
    with _patch_openai("not json"):
        score, rationale = judge_response(
            prompt="What is 2+2?",
            expected_behaviour="Returns 4",
            response="fish",
        )
    assert score == 0.0
    assert rationale.startswith("parse error:")


def test_judge_clamps_score():
    payload = json.dumps({"score": 1.5, "rationale": "too good"})
    with _patch_openai(payload):
        score, rationale = judge_response(
            prompt="What is 2+2?",
            expected_behaviour="Returns 4",
            response="4",
        )
    assert score == 1.0
    assert rationale == "too good"
