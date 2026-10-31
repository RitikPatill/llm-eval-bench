from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

import anthropic
import openai

from llm_eval_bench.judge import judge_response
from llm_eval_bench.result import CaseResult, RunResult, make_run_id, save_run
from llm_eval_bench.schema import EvalSuite, TestCase


def _resolve_model(case: TestCase, suite: EvalSuite, override: str | None) -> str:
    """Priority: override > case.model > suite.default_model. Raises ValueError if none."""
    model = override or case.model or suite.default_model
    if not model:
        raise ValueError(
            f"No model specified for case '{case.id}': set --model, case.model, or suite.default_model"
        )
    return model


def _call_model(
    prompt: str,
    model: str,
    base_url: str | None,
    api_key: str | None,
) -> str:
    """Routes to anthropic SDK if model starts with 'claude-', else openai SDK."""
    if model.startswith("claude-"):
        client_kwargs: dict = {}
        if api_key is not None:
            client_kwargs["api_key"] = api_key
        client = anthropic.Anthropic(**client_kwargs)
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    else:
        client_kwargs = {}
        if base_url is not None:
            client_kwargs["base_url"] = base_url
        if api_key is not None:
            client_kwargs["api_key"] = api_key
        client = openai.OpenAI(**client_kwargs)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return completion.choices[0].message.content or ""


def run_suite(
    suite: EvalSuite,
    suite_path: str,
    *,
    model_override: str | None = None,
    judge_model: str = "gpt-4o-mini",
    base_url: str | None = None,
    api_key: str | None = None,
    judge_base_url: str | None = None,
    judge_api_key: str | None = None,
    threshold: float = 0.5,
    on_result: Callable[[CaseResult], None] | None = None,
) -> RunResult:
    run_id = make_run_id()
    case_results: list[CaseResult] = []

    for case in suite.cases:
        model = _resolve_model(case, suite, model_override)
        response = _call_model(case.prompt, model, base_url, api_key)
        score, rationale = judge_response(
            prompt=case.prompt,
            expected_behaviour=case.expected_behaviour,
            response=response,
            judge_model=judge_model,
            base_url=judge_base_url,
            api_key=judge_api_key,
        )
        result = CaseResult(
            case_id=case.id,
            prompt=case.prompt,
            expected_behaviour=case.expected_behaviour,
            model=model,
            response=response,
            score=score,
            rationale=rationale,
            passed=score >= threshold,
        )
        case_results.append(result)
        if on_result is not None:
            on_result(result)

    run = RunResult(
        run_id=run_id,
        suite_name=suite.name,
        suite_path=suite_path,
        threshold=threshold,
        cases=case_results,
        created_at=datetime.utcnow().isoformat() + "Z",
    )
    save_run(run)
    return run
