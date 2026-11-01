from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class CaseResult(BaseModel):
    case_id: str
    prompt: str
    expected_behaviour: str
    model: str
    response: str
    score: float          # 0.0–1.0
    rationale: str
    passed: bool          # score >= threshold


class RunResult(BaseModel):
    run_id: str           # "20241031_143022"
    suite_name: str
    suite_path: str
    threshold: float
    cases: list[CaseResult]
    created_at: str       # ISO-8601


def save_run(run: RunResult, results_dir: Path = Path("results")) -> Path:
    """Writes results/<run_id>.json, creates dir if missing. Returns path."""
    results_dir.mkdir(parents=True, exist_ok=True)
    path = results_dir / f"{run.run_id}.json"
    path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_run(run_id: str, results_dir: Path = Path("results")) -> RunResult:
    """Loads and validates a previously saved run."""
    path = results_dir / f"{run_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Run not found: {path}")
    return RunResult.model_validate_json(path.read_text(encoding="utf-8"))


def make_run_id() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


def list_runs(results_dir: Path = Path("results")) -> list[RunResult]:
    """Returns all saved runs sorted newest-first. Returns [] if dir missing."""
    if not results_dir.exists():
        return []
    runs = []
    for path in results_dir.glob("*.json"):
        try:
            runs.append(RunResult.model_validate_json(path.read_text(encoding="utf-8")))
        except Exception:
            pass
    runs.sort(key=lambda r: r.run_id, reverse=True)
    return runs
