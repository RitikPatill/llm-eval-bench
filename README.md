# LLM Eval Bench

## What is LLM Eval Bench

LLM Eval Bench is a local-first evaluation harness for anyone building products on top of large language models. You write test cases in plain YAML — a prompt, an expected behaviour, and a scoring rubric — point it at any OpenAI-compatible endpoint or the Anthropic API, and it runs every case, judges each response with a secondary LLM call (LLM-as-judge pattern), and surfaces a pass/fail/score report in the terminal and a minimal web dashboard.

## Why it exists

Every serious LLM product team needs regression testing, but existing frameworks (PromptFoo, RAGAS, Braintrust) are either vendor-locked, heavy, or SaaS. LLM Eval Bench gives you a zero-dependency-on-cloud, fully inspectable harness that runs on `localhost` in under a minute. Flat JSON result files mean full reproducibility and easy diffing — no database, no account required.

## What works now (M2)

- Python package installable via `pip install -e .`
- `eval run` CLI entry point registered (stub — prints a not-yet-implemented message)
- `python -m llm_eval_bench` entry point wired up
- `pyproject.toml` with full dependency set declared (typer, rich, fastapi, uvicorn, jinja2, pydantic, pyyaml, openai, anthropic)
- MIT license, `.gitignore`, and test scaffold in place
- **Pydantic v2 schema** — `TestCase` and `EvalSuite` models with duplicate-ID validation (`src/llm_eval_bench/schema.py`)
- **YAML suite loader** — `load_suite(path)` reads and validates a YAML file into an `EvalSuite` (`src/llm_eval_bench/loader.py`)
- **Three bundled example suites** under `examples/`: `factuality.yaml`, `instruction_following.yaml`, `code_quality.yaml`
- **Unit tests** for happy-path loading, default fields, duplicate IDs, missing fields, and missing file (`tests/test_loader.py`) — all passing

The runner, scorer, and dashboard ship in later milestones.

## Quick start

```bash
# Install in editable mode
pip install -e .

# Confirm the CLI is wired (M1 — prints a stub message)
eval run

# Run an eval suite (available from M3)
eval run examples/factuality.yaml

# Serve the dashboard (available from M4)
eval serve
```

## Project structure

```
llm-eval-bench/
├── src/
│   └── llm_eval_bench/
│       ├── __init__.py       # package version (0.1.0)
│       ├── __main__.py       # python -m llm_eval_bench entry point
│       ├── cli.py            # typer CLI stub — eval run (others added per milestone)
│       ├── schema.py         # Pydantic v2 models: TestCase, EvalSuite
│       └── loader.py         # load_suite(path) — reads and validates a YAML suite
├── examples/
│   ├── factuality.yaml       # 5 factual-recall test cases
│   ├── instruction_following.yaml  # 5 formatting/constraint test cases
│   └── code_quality.yaml    # 5 Python code-generation test cases
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py         # smoke test scaffold
│   └── test_loader.py        # loader unit tests (happy path, validation, edge cases)
├── results/                  # run outputs (git-ignored, created at runtime)
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

## Roadmap

- [x] **M1** — scaffold + readme: package layout, pyproject.toml, README, license
- [x] **M2** — YAML schema + loader: define test-case schema with Pydantic, load suites
- [ ] **M3** — runner: call OpenAI-compatible and Anthropic endpoints, persist JSON results
- [ ] **M4** — LLM-as-judge scorer: secondary LLM call returning 0–1 score + rationale
- [ ] **M5** — FastAPI + Jinja2 dashboard: per-run pass rates, score history sparklines, diff view
- [ ] **M6** — polish: bundled example suites, `eval compare`, CI smoke test

## License

MIT — see [LICENSE](LICENSE).
