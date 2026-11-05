# LLM Eval Bench

> Lightweight local eval harness: define test cases in YAML, score with an LLM judge, track regressions in a web dashboard.

<!-- TODO: replace with a 5-10 second demo gif. Record with ScreenToGif on
     Windows or peek on macOS/Linux. The VHS tape script is at docs/demo.tape —
     run `vhs docs/demo.tape` if you have VHS installed. Save the output to
     docs/demo.gif and update the path here. -->

## What it is

LLM Eval Bench is a local-first regression-testing harness for LLM-powered products. You write test cases in plain YAML — a prompt, a free-text rubric describing expected behaviour, and optional tags — then point the tool at any OpenAI-compatible endpoint or the Anthropic API. The runner calls the target model for each case, forwards the response to a secondary judge model (LLM-as-judge pattern), and collects a 0–1 score plus a one-line rationale for every result.

Results land in timestamped JSON files under `results/`. A `rich`-powered CLI lets you list runs and diff two runs side-by-side. A minimal FastAPI + Jinja2 dashboard at `http://localhost:8000` shows per-run pass rates, per-case score history sparklines, and a regression/improvement diff view. No database, no cloud account, no account required.

## Quickstart

```bash
git clone https://github.com/RitikPatill/llm-eval-bench.git
cd llm-eval-bench

# Python 3.11+ required
pip install -e .

# Provide at least one API key (whichever you will use as the judge/target)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...   # only needed for claude-* target models

# Run the bundled factuality suite
eval run examples/factuality.yaml --model gpt-4o-mini

# Start the dashboard
eval serve
# open http://localhost:8000
```

## Usage

**Run a suite and inspect results in the terminal:**

```bash
eval run examples/instruction_following.yaml --model gpt-4o-mini --judge-model gpt-4o --threshold 0.7
```

The terminal shows a `rich` progress bar that updates per case with its score and pass/fail status, then prints a summary panel with the overall pass rate and the path to the saved JSON file.

**Compare two runs to catch regressions:**

```bash
eval list                                        # find run IDs
eval compare 20241031_143022 20241101_090000     # diff by run ID
```

Red rows are regressions; green rows are improvements. A summary line counts each category.

**Use a local model via an OpenAI-compatible endpoint:**

```bash
eval run examples/code_quality.yaml --model my-model --base-url http://localhost:11434/v1
```

**Persist defaults in `.evalrc.yaml`** (project root or `~`):

```yaml
judge_model: gpt-4o-mini
threshold: 0.5
results_dir: results
# base_url: http://localhost:11434/v1
```

Environment variables (`EVAL_JUDGE_MODEL`, `EVAL_BASE_URL`, `EVAL_THRESHOLD`, `EVAL_RESULTS_DIR`) always override the file.

**Write a test case** — the `expected_behaviour` field is a free-text rubric passed verbatim to the judge:

```yaml
suite: my_suite
cases:
  - id: capital-au
    prompt: "What is the capital of Australia?"
    expected_behaviour: >
      Must answer Canberra. Must not confuse the capital with Sydney or Melbourne.
    tags: [factuality]
```

## Architecture

```
┌──────────────┐     ┌────────┐     ┌───────────┐     ┌─────────────┐
│  YAML Suite  │────▶│ Loader │────▶│  Runner   │────▶│  Target LLM │
└──────────────┘     └────────┘     └─────┬─────┘     └──────┬──────┘
                                          │                   │ response
                                          │            ┌──────▼──────┐
                                          │            │  Judge LLM  │
                                          │            └──────┬──────┘
                                          │  CaseResult       │
                                    ┌─────▼───────────────────▼─────┐
                                    │       JSON Store (results/)    │
                                    └──────────┬──────────┬──────────┘
                                               │          │
                                        ┌──────▼──┐  ┌───▼──────┐
                                        │   CLI   │  │Dashboard │
                                        └─────────┘  └──────────┘
```

The **Loader** parses YAML into validated Pydantic models. The **Runner** dispatches each prompt to the target model, routing `claude-*` model names to the Anthropic SDK and everything else to the OpenAI-compatible client. Each response goes to the **Judge**, which returns a structured `{score, rationale}` JSON. The assembled `RunResult` is written as a timestamped JSON file; the CLI and Dashboard read from that store independently.

## Project structure

```
llm-eval-bench/
├── src/llm_eval_bench/
│   ├── cli.py            # typer CLI — eval run / list / compare / serve
│   ├── config.py         # EvalConfig — .evalrc.yaml + env var resolution
│   ├── schema.py         # Pydantic v2 models: TestCase, EvalSuite
│   ├── loader.py         # load_suite() — reads and validates a YAML suite
│   ├── runner.py         # run_suite() — orchestrates model calls + judge
│   ├── judge.py          # judge_response() — LLM-as-judge scorer
│   ├── result.py         # CaseResult, RunResult, save/load/list helpers
│   ├── dashboard.py      # FastAPI app — index, run-detail, compare routes
│   └── templates/        # Jinja2 HTML templates
├── docs/
│   └── demo.tape         # VHS script to regenerate demo.gif
├── examples/
│   ├── factuality.yaml            # 5 factual-recall cases
│   ├── instruction_following.yaml # 5 formatting/constraint cases
│   └── code_quality.yaml          # 5 Python code-generation cases
├── tests/                # pytest suite — runner, judge, dashboard, CLI, config
├── results/              # run outputs (git-ignored, created at runtime)
├── pyproject.toml
├── requirements.txt
└── LICENSE
```

## Roadmap

- [ ] Async runner — parallel model calls to reduce wall-clock time on large suites
- [ ] HTML/CSV export of run results for sharing outside the dashboard
- [ ] Anthropic-native judge support (currently judge requires an OpenAI-compatible endpoint)
- [ ] Per-tag pass-rate breakdown in the dashboard
- [ ] `eval watch` mode — re-run a suite automatically when YAML files change

## License

MIT — see [LICENSE](LICENSE).

---

Built autonomously by [autodev](https://github.com/RitikPatill/autodev),
a multi-agent orchestrator I designed. Each commit in this repo was
authored by me; the implementation work was performed by Sonnet under
the orchestrator's control. Read the orchestrator's README to see how.
