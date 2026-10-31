from pathlib import Path

import yaml
from pydantic import ValidationError  # noqa: F401 — re-exported for callers

from llm_eval_bench.schema import EvalSuite


def load_suite(path: str | Path) -> EvalSuite:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Suite file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return EvalSuite.model_validate(raw)
