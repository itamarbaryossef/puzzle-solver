# Puzzle Solver

A `nanoagent.plugin/v0001` plugin for visual reasoning by a text-only agent: matching shapes. Its
input is a puzzle drawn as text, a picture with a hole cut out and two to four candidate pieces, and
the agent must say which piece fills the hole exactly. Pieces are placed as drawn: they may be moved,
but never turned or flipped, so a piece that would fit only turned or mirrored is a trap. Unlike a
question with one answer key, a puzzle may have more than one right answer (two pieces may fit), so
the verifier tries the agent's piece on the puzzle itself, with no model.

A puzzle is drawn in `#` and `.`. In the picture, `#` is filled and `.` is the hole; in a piece, `#`
is part of the piece and `.` is empty, so a piece can be drawn inside a larger blank box:

```json
{
  "picture": ["######", "######", "#...##", "#.####", "######", "######"],
  "pieces": [
    {"name": "A", "rows": ["##", ".#", ".#"]},
    {"name": "B", "rows": ["###", "#.."]},
    {"name": "C", "rows": ["####"]}
  ]
}
```

The hole is `###` over `#..`, so B fills it. A is the same shape turned a quarter, which would fit
only if turned, and C is a different shape.

A puzzle must have an answer. It is refused unless:

- the picture is 2 to 12 rows and columns, every row the same length, and holds only `#` and `.`;
- the hole is 3 to 6 cells, all joined side to side;
- there are 2 to 4 pieces, each named one of `A` to `D`, no two alike;
- each piece is at most 4 rows and columns, holds only `#` and `.`, and has 1 to 8 `#` cells;
- at least one piece fills the hole.

Puzzles are kept this small so that DeepSeek V4 Flash's reasoning fits inside RUSH Lab's 2048-token
output limit.

## Tools

| Tool | Does | Code |
|---|---|---|
| `view_puzzle` | Reads the puzzle into the hole's cells and each piece's cells (as `[row, column]`), saves them as `puzzle.json` in the workspace, and returns them with the question; it solves nothing | `src/plugin/puzzle.py` |
| `find_fits` | Finds every piece that fills the hole as drawn; the `find-the-piece` task's pinned reference | `src/plugin/puzzle.py` |

### Tasks

| Task | Does | Runner |
|---|---|---|
| `find-the-piece` | Finds the piece that fills the hole in a picture exactly, as drawn | `agent`, with `view_puzzle`; reference `find_fits` |

The task's input is the puzzle, as above. Its output is `{"piece": "<A to D>"}`: the name of a
piece that fills the hole.

The verifier (`verifier/`) solves every puzzle on its own, apart from `src/plugin/`, and checks:

- `verify_input`: the puzzle keeps every rule above, including that some piece fits.
- `verify_output` of `view_puzzle`: the returned view is the `puzzle.json` saved in the workspace,
  the question is the task's, and the hole and each piece are the cells drawn in the input.
- `verify_output` of `find_fits`: the fitting pieces are exactly the verifier's own.
- `verify_task`: the puzzle and the pinned fits again, then the agent's answer, with its own message
  for each way to be wrong: no piece named, a name that is not one of the pieces, or a piece that
  does not fill the hole as drawn (`details` give its cells against the hole's, and whether it would
  fit if turned or if flipped). Any piece that fills the hole is right, scored 1; names ignore case
  and spaces.

## Layout

```text
.
├── nanoagent.yaml   # manifest (a slimconfig ManifestConfig): id, runtime, permissions, tools, tasks
├── contract.py      # each tool's and task's typed input and output: slimconfig Output classes
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env             # environment variable NAMEs this plugin needs, never values (none)
├── src/plugin/      # the MCP server (__main__.py) and the puzzle checks and tools (puzzle.py)
├── tests/           # test_puzzle.py (the tools), test_verifier.py (the verifier), evals/ (model runs)
├── ui/              # how the page draws the outputs: renderers.js and renderers.css
├── product/         # the product page a catalog shows: product.yaml and icon.svg
└── verifier/        # deterministic verifier package: view.py, fits.py and checks.py
```

`contract.py` is the one place a value's shape is declared. Its `Output` classes are the JSON
Schemas the server offers and the agent sees, and every input and output is built into its class
on the way in and out. A tool that fails raises; NanoAgent sees an MCP error. The plugin needs no
network, no API key, no data files and no randomness: every answer follows from the puzzle alone.

## Develop and run

Prerequisites: Git, Python 3.12 or later, and `uv`.

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
```

To see a puzzle's view and fits without an agent:

```bash
uv run python -c "
import json
from pathlib import Path
from slimconfig import build_output
from contract import PuzzleInput
from plugin.puzzle import find_fits, view_puzzle
given = build_output(json.loads(Path('tests/evals/inputs/04-mirror-trap.json').read_text()), PuzzleInput)
print(view_puzzle(given, Path('.')))
print(find_fits(given, Path('.')))
"
```

This writes `puzzle.json`, the view, to the current folder.

## Evaluating with a model

`tests/evals/` runs the `find-the-piece` task end to end with the model and limits RUSH Lab uses
(DeepSeek V4 Flash through OpenRouter, `tests/evals/agent.yaml`) on the 15 puzzles in
`tests/evals/inputs/`, each named for the case it tests: pieces turned a quarter or halfway, mirror
images, pieces a cell too big or too small, two fitting pieces, a hole on the picture's edge, a piece
drawn inside a blank border, 2 and 4 pieces, a 12 by 12 picture, and holes of 3 to 6 cells. `tests/test_puzzle.py`
checks each one's fits. It is its own uv project, which installs NanoAgent pinned to a commit of
github.com/RUSH-LAB/nanoagent, so it needs only Git, `uv` and an OpenRouter API key:

```bash
export OPENROUTER_API_KEY=...   # your own key; never commit it
uv run --project tests/evals python tests/evals/run.py
```

Each puzzle gets a folder `tests/evals/runs/<name>/` holding `result.json` (the agent's answer),
`reference.json` (the fits), `verdict.json` (the verifier's verdict), `messages.json` (the
conversation) and `run.log`. `tests/evals/runs/summary.md` tabulates them, and `all_inputs.json`,
`all_verdicts.json` and `all_run_logs.log` gather every run's input, verdict and log. A folder that
already exists is not rerun, so delete `tests/evals/runs/` to start over. The fits and verdicts are
deterministic, but the model's answers can differ from run to run.

Publishing checks every plugin rule: push the plugin to a public GitHub repository and submit its
URL in the RUSH Lab marketplace. In the plugin's chat, paste a puzzle such as the one above,
and the result card shows the verifier's verdict.
