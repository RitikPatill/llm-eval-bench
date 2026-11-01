from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import llm_eval_bench.dashboard as dashboard_module
from llm_eval_bench.dashboard import app
from llm_eval_bench.result import CaseResult, RunResult

client = TestClient(app)


def make_run_result(
    tmp_results: Path,
    run_id: str,
    suite_name: str = "test-suite",
    case_ids: list[str] | None = None,
) -> RunResult:
    if case_ids is None:
        case_ids = ["case-1"]
    cases = [
        CaseResult(
            case_id=cid,
            prompt=f"Prompt for {cid}",
            expected_behaviour="Should answer correctly",
            model="gpt-4o-mini",
            response=f"Response for {cid}",
            score=0.8,
            rationale="Looks good",
            passed=True,
        )
        for cid in case_ids
    ]
    run = RunResult(
        run_id=run_id,
        suite_name=suite_name,
        suite_path=f"examples/{suite_name}.yaml",
        threshold=0.5,
        cases=cases,
        created_at="2024-10-31T14:30:00",
    )
    tmp_results.mkdir(parents=True, exist_ok=True)
    (tmp_results / f"{run_id}.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    return run


@pytest.fixture(autouse=True)
def set_results_dir(tmp_path):
    results_dir = tmp_path / "results"
    dashboard_module.RESULTS_DIR = results_dir
    yield results_dir
    dashboard_module.RESULTS_DIR = Path("results")


def test_index_empty(set_results_dir):
    response = client.get("/")
    assert response.status_code == 200
    assert "No runs found" in response.text


def test_index_lists_runs(set_results_dir):
    make_run_result(set_results_dir, "20241031_143022")
    response = client.get("/")
    assert response.status_code == 200
    assert "20241031_143022" in response.text


def test_run_detail_ok(set_results_dir):
    make_run_result(set_results_dir, "20241031_143022", case_ids=["case-alpha"])
    response = client.get("/runs/20241031_143022")
    assert response.status_code == 200
    assert "case-alpha" in response.text
    assert "Looks good" in response.text


def test_run_detail_not_found(set_results_dir):
    response = client.get("/runs/nonexistent_run_id")
    assert response.status_code == 404


def test_compare_ok(set_results_dir):
    make_run_result(set_results_dir, "20241031_120000", case_ids=["c1", "c2"])
    make_run_result(set_results_dir, "20241031_130000", case_ids=["c1", "c2"])
    response = client.get("/compare?a=20241031_120000&b=20241031_130000")
    assert response.status_code == 200
    assert "c1" in response.text
    assert "c2" in response.text
    # delta column header present
    assert "Δ" in response.text


def test_compare_missing_run(set_results_dir):
    make_run_result(set_results_dir, "20241031_120000")
    response = client.get("/compare?a=20241031_120000&b=bad_run_id")
    assert response.status_code == 404
