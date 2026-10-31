from __future__ import annotations

import json

import openai

JUDGE_PROMPT_TEMPLATE = """\
You are an impartial evaluator. Score the assistant response below.

## Prompt
{prompt}

## Expected behaviour (rubric)
{expected_behaviour}

## Assistant response
{response}

Return ONLY a JSON object with exactly two keys:
  "score"     – float 0.0 (fail) to 1.0 (perfect)
  "rationale" – one sentence explaining the score

Example: {{"score": 0.8, "rationale": "Correct answer but included unnecessary caveats."}}
"""


def judge_response(
    *,
    prompt: str,
    expected_behaviour: str,
    response: str,
    judge_model: str = "gpt-4o-mini",
    base_url: str | None = None,
    api_key: str | None = None,
) -> tuple[float, str]:
    """Returns (score, rationale). Falls back to (0.0, 'parse error: ...') on bad JSON."""
    client_kwargs: dict = {}
    if base_url is not None:
        client_kwargs["base_url"] = base_url
    if api_key is not None:
        client_kwargs["api_key"] = api_key

    client = openai.OpenAI(**client_kwargs)

    content = JUDGE_PROMPT_TEMPLATE.format(
        prompt=prompt,
        expected_behaviour=expected_behaviour,
        response=response,
    )

    create_kwargs: dict = {
        "model": judge_model,
        "messages": [{"role": "user", "content": content}],
    }
    if judge_model.startswith("gpt-"):
        create_kwargs["response_format"] = {"type": "json_object"}

    completion = client.chat.completions.create(**create_kwargs)
    raw = completion.choices[0].message.content or ""

    try:
        data = json.loads(raw)
        score = float(data["score"])
        score = max(0.0, min(1.0, score))
        rationale = str(data["rationale"])
        return score, rationale
    except Exception as exc:
        return 0.0, f"parse error: {exc}"
