from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from llm_eval_bench.loader import load_suite
from llm_eval_bench.result import CaseResult
from llm_eval_bench.runner import run_suite

app = typer.Typer()


@app.command()
def run(
    suite: Path = typer.Argument(..., help="Path to YAML suite file"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model for all cases"),
    judge_model: str = typer.Option("gpt-4o-mini", "--judge-model", help="Model used to score responses"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="OpenAI-compatible base URL"),
    threshold: float = typer.Option(0.5, "--threshold", help="Min score to count as pass"),
):
    """Run an eval suite and score each response with an LLM judge."""
    from rich.console import Console
    console = Console()

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
            judge_model=judge_model,
            base_url=base_url,
            threshold=threshold,
            on_result=on_result,
        )

    passed = sum(1 for r in results if r.passed)
    pass_rate = passed / total if total else 0.0

    console.print(
        Panel(
            f"[bold]Suite:[/bold] {eval_suite.name}\n"
            f"[bold]Cases:[/bold] {total}  "
            f"[bold]Passed:[/bold] {passed}  "
            f"[bold]Pass rate:[/bold] {pass_rate:.0%}\n"
            f"[bold]Results saved to:[/bold] results/{run_result.run_id}.json",
            title="[green]Eval complete[/green]",
        )
    )


if __name__ == "__main__":
    app()
