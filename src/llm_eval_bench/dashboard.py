from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from llm_eval_bench import result as result_store

RESULTS_DIR: Path = Path("results")

app = FastAPI(title="LLM Eval Bench")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _pass_rate(run) -> float:
    if not run.cases:
        return 0.0
    return sum(c.passed for c in run.cases) / len(run.cases)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    runs = result_store.list_runs(RESULTS_DIR)
    run_rows = [
        {
            "run": r,
            "pass_rate": _pass_rate(r),
            "passed": sum(c.passed for c in r.cases),
        }
        for r in runs
    ]
    return templates.TemplateResponse(request, "index.html", {"run_rows": run_rows})


@app.get("/runs/{run_id}", response_class=HTMLResponse)
def run_detail(request: Request, run_id: str):
    try:
        run = result_store.load_run(run_id, RESULTS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return templates.TemplateResponse(
        request,
        "run_detail.html",
        {
            "run": run,
            "pass_rate": _pass_rate(run),
            "passed": sum(c.passed for c in run.cases),
        },
    )


@app.get("/compare", response_class=HTMLResponse)
def compare(request: Request, a: str, b: str):
    try:
        run_a = result_store.load_run(a, RESULTS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{a}' not found")
    try:
        run_b = result_store.load_run(b, RESULTS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run '{b}' not found")

    scores_a = {c.case_id: c.score for c in run_a.cases}
    scores_b = {c.case_id: c.score for c in run_b.cases}
    all_ids = list(dict.fromkeys([c.case_id for c in run_a.cases] + [c.case_id for c in run_b.cases]))

    rows = []
    for case_id in all_ids:
        sa = scores_a.get(case_id)
        sb = scores_b.get(case_id)
        delta = (sb - sa) if sa is not None and sb is not None else None
        rows.append({"case_id": case_id, "score_a": sa, "score_b": sb, "delta": delta})

    return templates.TemplateResponse(
        request,
        "compare.html",
        {"run_a": run_a, "run_b": run_b, "rows": rows},
    )
