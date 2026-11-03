from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
import yaml
from pydantic import BaseModel


class EvalConfig(BaseModel):
    judge_model: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    threshold: float = 0.5
    results_dir: str = "results"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


def load_config() -> EvalConfig:
    """Load config from YAML files and env vars.

    Search order (later wins): built-in defaults → ~/.evalrc.yaml → ./.evalrc.yaml → env vars.
    """
    merged: dict = {}

    # Load YAML files in order (home first, then cwd — cwd wins)
    for yaml_path in [Path.home() / ".evalrc.yaml", Path(".evalrc.yaml")]:
        if yaml_path.exists():
            try:
                data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
                if data is not None:
                    if not isinstance(data, dict):
                        raise typer.BadParameter(
                            f"Invalid .evalrc.yaml at {yaml_path}: expected a YAML mapping"
                        )
                    merged.update(data)
            except typer.BadParameter:
                raise
            except Exception as e:
                raise typer.BadParameter(f"Failed to parse {yaml_path}: {e}") from e

    # Overlay env vars (always win over YAML)
    env_map = {
        "EVAL_JUDGE_MODEL": "judge_model",
        "EVAL_BASE_URL": "base_url",
        "EVAL_THRESHOLD": "threshold",
        "EVAL_RESULTS_DIR": "results_dir",
        "OPENAI_API_KEY": "openai_api_key",
        "ANTHROPIC_API_KEY": "anthropic_api_key",
    }
    for env_key, field in env_map.items():
        val = os.environ.get(env_key)
        if val is not None:
            merged[field] = val

    # threshold may arrive as a string from env — coerce to float
    if "threshold" in merged and isinstance(merged["threshold"], str):
        try:
            merged["threshold"] = float(merged["threshold"])
        except ValueError as e:
            raise typer.BadParameter(f"EVAL_THRESHOLD must be a float: {e}") from e

    return EvalConfig(**merged)
