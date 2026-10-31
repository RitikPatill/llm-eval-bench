# LLM Eval Bench

## What is LLM Eval Bench

LLM Eval Bench is a local-first evaluation harness for anyone building products on top of large language models. You write test cases in plain YAML — a prompt, an expected behaviour, and a scoring rubric — point it at any OpenAI-compatible endpoint or the Anthropic API, and it runs every case, judges each response with a secondary LLM call (LLM-as-judge pattern), and surfaces a pass/fail/score report in the terminal and a minimal web dashboard.

## Why it exists

Every serious LLM product team needs regression testing, but existing frameworks (PromptFoo, RAGAS, Braintrust) are either vendor-locked, heavy, or SaaS. LLM Eval Bench gives you a zero-dependency-on-cloud, fully inspectable harness that runs on `localhost` in under a minute. Flat JSON result files mean full reproducibility and easy diffing — no database, no account required.

## What works now (M1)

- Python package installable via `pip install -e .`
- `eval run` CLI entry point registered (stub — prints a not-yet-implemented message)
- `python -m llm_eval_bench` entry point wired up
- `pyproject.toml` with full dependency set declared (typer, rich, fastapi, uvicorn, jinja2, pydantic, pyyaml, openai, anthropic)
- MIT license, `.gitignore`, and test scaffold in place

Nothing produces output yet; the runner, scorer, and dashboard ship in later milestones.

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
│       └── cli.py            # typer CLI stub — eval run (others added per milestone)
├── examples/                 # placeholder; bundled YAML suites added in M6
├── tests/
│   ├── __init__.py
│   └── test_smoke.py         # smoke test scaffold
├── results/                  # run outputs (git-ignored, created at runtime)
├── pyproject.toml
├── requirements.txt
├── LICENSE
└── README.md
```

## Roadmap

- [x] **M1** — scaffold + readme: package layout, pyproject.toml, README, license
- [ ] **M2** — YAML schema + loader: define test-case schema with Pydantic, load suites
- [ ] **M3** — runner: call OpenAI-compatible and Anthropic endpoints, persist JSON results
- [ ] **M4** — LLM-as-judge scorer: secondary LLM call returning 0–1 score + rationale
- [ ] **M5** — FastAPI + Jinja2 dashboard: per-run pass rates, score history sparklines, diff view
- [ ] **M6** — polish: bundled example suites, `eval compare`, CI smoke test

## License

MIT — see [LICENSE](LICENSE).
