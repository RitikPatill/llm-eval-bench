# LLM Eval Bench — VHS tape
# Records a terminal demo GIF showing the three main commands.
#
# Prerequisites (choose one):
#   macOS/Linux:  brew install vhs          (or: go install github.com/charmbracelet/vhs@latest)
#   Windows:      run inside WSL2            (or: docker run --rm -v $PWD:/vhs ghcr.io/charmbracelet/vhs docs/demo.tape)
#
# To record:
#   1. pip install -e .
#   2. Set OPENAI_API_KEY (or pre-populate results/ with fixture JSON — see notes below)
#   3. vhs docs/demo.tape          → produces docs/demo.gif
#
# Fixture-only recording (no API key needed):
#   Copy two JSON files from tests/fixtures/ (if they exist) into results/ and
#   skip the `eval run` step or redirect it to a pre-recorded run.

Output docs/demo.gif

Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Dracula"

# ── Title splash ───────────────────────────────────────────────────────────────
Type "# LLM Eval Bench — terminal demo"
Enter
Sleep 500ms

# ── Run the factuality suite ───────────────────────────────────────────────────
Type "eval run examples/factuality.yaml --model gpt-4o-mini"
Sleep 300ms
Enter
Sleep 4s

# ── List all recorded runs ─────────────────────────────────────────────────────
Type "eval list"
Enter
Sleep 2s

# ── Compare two runs ───────────────────────────────────────────────────────────
Type "eval compare 20241031_143022 20241101_090000"
Enter
Sleep 2s

# ── Launch the dashboard ───────────────────────────────────────────────────────
Type "eval serve &"
Enter
Sleep 2s
