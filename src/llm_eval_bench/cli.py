from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from llm_eval_bench.config import load_config
from llm_eval_bench.loader import load_suite
from llm_eval_bench.result import CaseResult, load_run, list_runs, save_run
from llm_eval_bench.runner import run_suite

app = typer.Typer()


@app.command()
def run(
    suite: Path = typer.Argument(..., help="Path to YAML suite file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model for all cases"),
    judge_model: Optional[str] = typer.Option(None, "--judge-model", help="Model used to score responses"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="OpenAI-compatible base URL"),
    threshold: Optional[float] = typer.Option(None, "--threshold", help="Min score to count as pass"),
    results_dir: Optional[Path] = typer.Option(None, "--results-dir", help="Directory to store results"),
):
    """Run an eval suite and score each response with an LLM judge."""
    from rich.console import Console
    console = Console()

    cfg = load_config()
    resolved_judge_model = judge_model or cfg.judge_model
    resolved_base_url = base_url or cfg.base_url
    resolved_threshold = threshold if threshold is not None else cfg.threshold
    resolved_results_dir = results_dir or Path(cfg.results_dir)

    eval_suite = load_suite(suite)
    total = len(eval_suite.cases)

    results: list[CaseResult] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task(f"Running {eval_suite.name}…", total=total)

        def on_result(result: CaseResult) -> None:
            icon = "✓" if result.passed else "✗"
            progress.advance(task_id)
            progress.update(
                task_id,
                description=f"{icon} [{result.case_id}] score={result.score:.2f}",
            )
            results.append(result)

        run_result = run_suite(
            eval_suite,
            str(suite),
            model_override=model,
            judge_model=resolved_judge_model,
            base_url=resolved_base_url,
            threshold=resolved_threshold,
            on_result=on_result,
        )

    save_run(run_result, resolved_results_dir)

    passed = sum(1 for r in results if r.passed)
    pass_rate = passed / total if total else 0.0

    console.print(
        Panel(
            f"[bold]Suite:[/bold] {eval_suite.name}\n"
            f"[bold]Cases:[/bold] {total}  "
            f"[bold]Passed:[/bold] {passed}  "
            f"[bold]Pass rate:[/bold] {pass_rate:.0%}\n"
            f"[bold]Results saved to:[/bold] {resolved_results_dir}/{run_result.run_id}.json",
            title="[green]Eval complete[/green]",
        )
    )


@app.command("list")
def list_runs_cmd(
    results_dir: Optional[Path] = typer.Option(None, "--results-dir", help="Results directory"),
) -> None:
    """List all past eval runs."""
    from rich.console import Console
    console = Console()

    cfg = load_config()
    resolved_results_dir = results_dir or Path(cfg.results_dir)

    runs = list_runs(resolved_results_dir)

    if not runs:
        console.print(f"[yellow]No runs found in {resolved_results_dir}[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Eval Runs")
    table.add_column("Run ID", style="cyan")
    table.add_column("Suite")
    table.add_column("Cases", justify="right")
    table.add_column("Passed", justify="right")
    table.add_column("Pass Rate", justify="right")
    table.add_column("Created At")

    for r in runs:
        total = len(r.cases)
        passed = sum(1 for c in r.cases if c.passed)
        pass_rate = passed / total if total else 0.0
        table.add_row(
            r.run_id,
            r.suite_name,
            str(total),
            str(passed),
            f"{pass_rate:.0%}",
            r.created_at,
        )

    console.print(table)


@app.command()
def compare(
    run_id_a: str = typer.Argument(..., help="Baseline run ID"),
    run_id_b: str = typer.Argument(..., help="Comparison run ID"),
    results_dir: Optional[Path] = typer.Option(None, "--results-dir", help="Results directory"),
) -> None:
    """Compare two eval runs, highlighting regressions and improvements."""
    from rich.console import Console
    console = Console()

    cfg = load_config()
    resolved_results_dir = results_dir or Path(cfg.results_dir)

    try:
        run_a = load_run(run_id_a, resolved_results_dir)
        run_b = load_run(run_id_b, resolved_results_dir)
    except FileNotFoundError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    scores_a = {c.case_id: c.score for c in run_a.cases}
    scores_b = {c.case_id: c.score for c in run_b.cases}

    all_case_ids = sorted(scores_a.keys() | scores_b.keys())

    table = Table(title=f"Compare {run_id_a} vs {run_id_b}")
    table.add_column("Case ID", style="cyan")
    table.add_column("Score A", justify="right")
    table.add_column("Score B", justify="right")
    table.add_column("Delta", justify="right")
    table.add_column("Status")

    regressions = 0
    improvements = 0
    unchanged = 0

    for case_id in all_case_ids:
        score_a = scores_a.get(case_id)
        score_b = scores_b.get(case_id)

        score_a_str = f"{score_a:.2f}" if score_a is not None else "—"
        score_b_str = f"{score_b:.2f}" if score_b is not None else "—"

        if score_a is not None and score_b is not None:
            delta = score_b - score_a
            delta_str = f"{delta:+.2f}"
            if delta < -0.01:
                status = "regression"
                row_style = "red"
                regressions += 1
            elif delta > 0.01:
                status = "improvement"
                row_style = "green"
                improvements += 1
            else:
                status = "unchanged"
                row_style = ""
                unchanged += 1
        else:
            delta_str = "—"
            status = "only in one run"
            row_style = ""

        table.add_row(case_id, score_a_str, score_b_str, delta_str, status, style=row_style)

    console.print(table)
    console.print(
        f"{regressions} regression(s), {improvements} improvement(s), {unchanged} unchanged"
    )


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    results_dir: Path = typer.Option(Path("results"), "--results-dir", help="Results directory"),
):
    """Start the web dashboard."""
    import uvicorn
    import llm_eval_bench.dashboard as dashboard_module
    dashboard_module.RESULTS_DIR = results_dir
    uvicorn.run(dashboard_module.app, host=host, port=port)


if __name__ == "__main__":
    app()
