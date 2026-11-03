from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from llm_eval_bench.cli import app
from llm_eval_bench.result import CaseResult, RunResult, save_run

runner = CliRunner()


def _make_case(case_id: str, score: float, passed: bool) -> CaseResult:
    return CaseResult(
        case_id=case_id,
        prompt="What is 2+2?",
        expected_behaviour="Should return 4",
        model="gpt-4o-mini",
        response="4",
        score=score,
        rationale="Correct",
        passed=passed,
    )


def _make_run(run_id: str, suite_name: str, cases: list[CaseResult]) -> RunResult:
    return RunResult(
        run_id=run_id,
        suite_name=suite_name,
        suite_path="examples/factuality.yaml",
        threshold=0.5,
        cases=cases,
        created_at=datetime.utcnow().isoformat(),
    )


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list", "--results-dir", str(tmp_path / "results")])
    assert result.exit_code == 0
    assert "No runs found" in result.output


def test_list_with_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    run_a = _make_run("20240101_120000", "factuality", [_make_case("q1", 0.9, True)])
    run_b = _make_run("20240102_120000", "factuality", [_make_case("q1", 0.4, False)])
    save_run(run_a, results_dir)
    save_run(run_b, results_dir)

    result = runner.invoke(app, ["list", "--results-dir", str(results_dir)])
    assert result.exit_code == 0
    assert "20240101_120000" in result.output
    assert "20240102_120000" in result.output


def test_compare_regression(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    run_a = _make_run("run_a", "factuality", [_make_case("q1", 0.9, True)])
    run_b = _make_run("run_b", "factuality", [_make_case("q1", 0.4, False)])
    save_run(run_a, results_dir)
    save_run(run_b, results_dir)

    result = runner.invoke(app, ["compare", "run_a", "run_b", "--results-dir", str(results_dir)])
    assert result.exit_code == 0
    assert "1 regression(s)" in result.output


def test_compare_improvement(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    run_a = _make_run("run_a", "factuality", [_make_case("q1", 0.4, False)])
    run_b = _make_run("run_b", "factuality", [_make_case("q1", 0.9, True)])
    save_run(run_a, results_dir)
    save_run(run_b, results_dir)

    result = runner.invoke(app, ["compare", "run_a", "run_b", "--results-dir", str(results_dir)])
    assert result.exit_code == 0
    assert "1 improvement(s)" in result.output


def test_compare_missing_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    result = runner.invoke(app, ["compare", "nonexistent_a", "nonexistent_b", "--results-dir", str(results_dir)])
    assert result.exit_code == 1


def test_compare_case_only_in_one_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results_dir = tmp_path / "results"
    run_a = _make_run("run_a", "factuality", [_make_case("q1", 0.8, True)])
    run_b = _make_run(
        "run_b",
        "factuality",
        [_make_case("q1", 0.8, True), _make_case("q2", 0.6, True)],
    )
    save_run(run_a, results_dir)
    save_run(run_b, results_dir)

    result = runner.invoke(app, ["compare", "run_a", "run_b", "--results-dir", str(results_dir)])
    assert result.exit_code == 0
    assert "—" in result.output
