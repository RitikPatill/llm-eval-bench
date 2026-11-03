from __future__ import annotations

import pytest
import typer

from llm_eval_bench.config import EvalConfig, load_config


def test_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # Remove any env vars that might interfere
    for key in ["EVAL_JUDGE_MODEL", "EVAL_BASE_URL", "EVAL_THRESHOLD", "EVAL_RESULTS_DIR",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    cfg = load_config()
    assert cfg.judge_model == "gpt-4o-mini"
    assert cfg.base_url is None
    assert cfg.threshold == 0.5
    assert cfg.results_dir == "results"


def test_yaml_override(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ["EVAL_JUDGE_MODEL", "EVAL_BASE_URL", "EVAL_THRESHOLD", "EVAL_RESULTS_DIR",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)

    (tmp_path / ".evalrc.yaml").write_text("judge_model: claude-3-5-haiku-20241022\n")
    cfg = load_config()
    assert cfg.judge_model == "claude-3-5-haiku-20241022"


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".evalrc.yaml").write_text("judge_model: claude-3-5-haiku-20241022\n")
    monkeypatch.setenv("EVAL_JUDGE_MODEL", "gpt-4o")

    cfg = load_config()
    assert cfg.judge_model == "gpt-4o"


def test_missing_yaml_ok(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ["EVAL_JUDGE_MODEL", "EVAL_BASE_URL", "EVAL_THRESHOLD", "EVAL_RESULTS_DIR",
                "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    # No .evalrc.yaml present — should not raise
    cfg = load_config()
    assert isinstance(cfg, EvalConfig)


def test_invalid_yaml_raises(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    # Write a YAML file that is a scalar, not a mapping
    (tmp_path / ".evalrc.yaml").write_text("- this\n- is a list\n")
    with pytest.raises(typer.BadParameter):
        load_config()
