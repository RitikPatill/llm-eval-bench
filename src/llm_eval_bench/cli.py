import typer

app = typer.Typer()


@app.command()
def run():
    """Run an eval suite (coming in M3)."""
    print("llm-eval-bench v0.1.0 — run not yet implemented")


if __name__ == "__main__":
    app()
