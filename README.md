# LLM Eval Bench

## What is LLM Eval Bench

LLM Eval Bench is a local-first evaluation harness for anyone building products on top of large language models. You write test cases in plain YAML — a prompt, an expected behaviour, and a scoring rubric — point it at any OpenAI-compatible endpoint or the Anthropic API, and it runs every case, judges each response with a secondary LLM call (LLM-as-judge pattern), and surfaces a pass/fail/score report in the terminal and a minimal web dashboard.

## Why it exists

Every serious LLM product team needs regression testing, but existing frameworks (PromptFoo, RAGAS, Braintrust) are either vendor-locked, heavy, or SaaS. LLM Eval Bench gives you a zero-dependency-on-cloud, fully inspectable harness that runs on `localhost` in under a minute. Flat JSON result files mean full reproducibility and easy diffing — no database, no account required.

## What works now (M4)

- Python package installable via `pip install -e .`
- **`eval run <suite.yaml>`** — fully working CLI command; `rich` progress bar updates per-case with score and pass/fail as each result lands; prints a summary panel (pass count, pass rate, results path) on completion
- **Runner** — calls target model (OpenAI-compatible or Anthropic) per test case, routes via SDK based on model name (`claude-*` → Anthropic, everything else → OpenAI)
- **LLM-as-judge scorer** — calls a judge model (OpenAI-compatible only; default `gpt-4o-mini`) with a structured rubric prompt; returns `{score, rationale}` JSON; score clamped to [0.0, 1.0]; falls back to `(0.0, "parse error: …")` on malformed output
- **JSON persistence** — each run saved as `results/<run_id>.json` (git-ignored); run ID is a UTC timestamp (`YYYYMMDD_HHMMSS`)
- **Pydantic v2 schema** — `TestCase`, `EvalSuite`, `CaseResult`, `RunResult` models
- **YAML suite loader** — `load_suite(path)` reads and validates YAML into `EvalSuite`
- **Three bundled example suites** under `examples/`: `factuality.yaml`, `instruction_following.yaml`, `code_quality.yaml`
- **Unit tests** — runner (model resolution, SDK routing, end-to-end with mocks), judge (JSON parsing, fallback, score clamping), and dashboard (all routes) — all passing
- **`eval serve`** — starts a FastAPI + Jinja2 dashboard at `http://localhost:8000`; index lists all runs with pass rates; run-detail page shows per-case scores and prompt/response accordions; compare page diffs two runs side-by-side with regression/improvement highlighting

## Quick start

```bash
# Install in editable mode
pip install -e .

# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...

# Run an eval suite (uses gpt-4o-mini as both target and judge by default)
eval run examples/factuality.yaml --model gpt-4o-mini

# Override the judge model
eval run examples/instruction_following.yaml --model gpt-4o-mini --judge-model gpt-4o

# Use an OpenAI-compatible local endpoint
eval run examples/code_quality.yaml --model my-local-model --base-url http://localhost:11434/v1

# Set a custom pass threshold (default 0.5)
eval run examples/factuality.yaml --model gpt-4o-mini --threshold 0.7

# Serve the dashboard (available from M4)
eval serve
```

## CLI reference

```
eval run <suite>           Run an eval suite
  --model / -m             Override model for all cases
  --judge-model            Model used to score responses (default: gpt-4o-mini)
  --base-url               OpenAI-compatible base URL (omit for official OpenAI)
  --threshold              Min score to count as pass (default: 0.5)

eval serve                 Start the web dashboard at http://localhost:8000
  --host                   Bind host (default: 127.0.0.1)
  --port / -p              Bind port (default: 8000)
  --results-dir            Results directory (default: results/)
```

## Project structure

```
llm-eval-bench/
├── src/
│   └── llm_eval_bench/
│       ├── __init__.py       # package version (0.1.0)
│       ├── __main__.py       # python -m llm_eval_bench entry point
│       ├── cli.py            # typer CLI — eval run with rich progress
│       ├── schema.py         # Pydantic v2 models: TestCase, EvalSuite
│       ├── loader.py         # load_suite(path) — reads and validates a YAML suite
│       ├── runner.py         # run_suite() — orchestrates model calls + judge
│       ├── judge.py          # judge_response() — LLM-as-judge scorer
│       ├── result.py         # CaseResult, RunResult, save_run(), load_run(), list_runs()
│       ├── dashboard.py      # FastAPI app — index, run-detail, compare routes
│       └── templates/        # Jinja2 HTML templates (base, index, run_detail, compare)
├── examples/
│   ├── factuality.yaml       # 5 factual-recall test cases
│   ├── instruction_following.yaml  # 5 formatting/constraint test cases
│   └── code_quality.yaml    # 5 Python code-generation test cases
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py         # smoke test scaffold
│   ├── test_loader.py        # loader unit tests
│   ├── test_runner.py        # runner unit tests (mocked API calls)
│   ├── test_judge.py         # judge unit tests (mocked API calls)
│   └── test_dashboard.py     # dashboard route tests (TestClient)
├── results/                  # run outputs (git-ignored, created at runtime)
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

## Roadmap

- [x] **M1** — scaffold + readme: package layout, pyproject.toml, README, license
- [x] **M2** — YAML schema + loader: define test-case schema with Pydantic, load suites
- [x] **M3** — runner + LLM-as-judge scorer: call models, score with judge, persist JSON results
- [x] **M4** — FastAPI + Jinja2 dashboard: `eval serve` command, index/run-detail/compare pages
- [ ] **M5** — polish: CI smoke test, extended example suites
- [ ] **M6** — polish: CI smoke test, extended example suites

## License

MIT — see [LICENSE](LICENSE).
