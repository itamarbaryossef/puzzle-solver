from __future__ import annotations

import json
from pathlib import Path

from slimconfig import plain_output

from contract import FitsOutput, PieceCells, PuzzleInput, ViewOutput

QUESTION = "Which piece fills the hole exactly, as drawn, without turning or flipping it?"
FILLED, EMPTY = "#", "."
SIDE = (2, 12)  # fewest and most rows, and columns, in the picture
HOLE = (3, 6)  # fewest and most cells in the hole
PIECES = (2, 4)  # fewest and most pieces
NAMES = "ABCD"
PIECE_SIDE = 4  # most rows, and columns, in a piece
PIECE_CELLS = (1, 8)  # fewest and most cells in a piece
VIEW_FILE = "puzzle.json"


def cells(rows: list[str], mark: str) -> set[tuple[int, int]]:
    """Every (row, column) in ``rows`` holding ``mark``."""
    return {(row, column) for row, line in enumerate(rows) for column, char in enumerate(line) if char == mark}


def trim(shape) -> frozenset[tuple[int, int]]:
    """``shape`` moved so its top row and its left column are 0: two shapes match when their trims are equal."""
    top = min(row for row, _ in shape)
    left = min(column for _, column in shape)
    return frozenset((row - top, column - left) for row, column in shape)


def _connected(shape) -> bool:
    shape = set(shape)
    seen, todo = set(), [next(iter(shape))]
    while todo:
        row, column = todo.pop()
        if (row, column) in seen:
            continue
        seen.add((row, column))
        for near in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
            if near in shape:
                todo.append(near)
    return seen == shape


def _drawing_problem(rows: list[str], what: str, fewest: int, most: int) -> str | None:
    if not fewest <= len(rows) <= most or not fewest <= len(rows[0]) <= most:
        return f"{what} must be {fewest} to {most} rows and columns"
    if any(len(row) != len(rows[0]) for row in rows):
        return f"{what}'s rows must all be the same length"
    if any(set(row) - {FILLED, EMPTY} for row in rows):
        return f"{what} may hold only '{FILLED}' and '{EMPTY}'"
    return None


def puzzle_problem(given: PuzzleInput) -> str | None:
    """What makes ``given`` not a puzzle with an answer, or None."""
    problem = _drawing_problem(given.picture, "the picture", *SIDE)
    if problem:
        return problem
    hole = cells(given.picture, EMPTY)
    if not HOLE[0] <= len(hole) <= HOLE[1]:
        return f"the hole must be {HOLE[0]} to {HOLE[1]} cells, not {len(hole)}"
    if not _connected(hole):
        return "the hole must be one piece: its cells joined side to side"
    if not PIECES[0] <= len(given.pieces) <= PIECES[1]:
        return f"there must be {PIECES[0]} to {PIECES[1]} pieces, not {len(given.pieces)}"
    names = [piece.name for piece in given.pieces]
    if any(name not in NAMES for name in names) or len(set(names)) != len(names):
        return f"each piece must have its own name, one of {', '.join(NAMES)}"
    for piece in given.pieces:
        problem = _drawing_problem(piece.rows, f"piece {piece.name}", 1, PIECE_SIDE)
        if problem:
            return problem
        if not PIECE_CELLS[0] <= len(cells(piece.rows, FILLED)) <= PIECE_CELLS[1]:
            return f"piece {piece.name} must have {PIECE_CELLS[0]} to {PIECE_CELLS[1]} '{FILLED}' cells"
    if not _fits(given):
        return "no piece fills the hole"
    return None


def _fits(given: PuzzleInput) -> list[str]:
    """Every piece whose cells, only moved, are the hole's: a piece is never turned or flipped."""
    hole = trim(cells(given.picture, EMPTY))
    return [piece.name for piece in given.pieces if trim(cells(piece.rows, FILLED)) == hole]


def _checked(given: PuzzleInput) -> PuzzleInput:
    problem = puzzle_problem(given)
    if problem:
        raise ValueError(problem)
    return given


def view_puzzle(given: PuzzleInput, workspace: Path) -> ViewOutput:
    """The hole and each piece as lists of cells, as a vision model might read them; it solves nothing."""
    _checked(given)
    pieces = [
        PieceCells(piece.name, [list(cell) for cell in sorted(trim(cells(piece.rows, FILLED)))])
        for piece in given.pieces
    ]
    hole = [list(cell) for cell in sorted(cells(given.picture, EMPTY))]
    output = ViewOutput(path=VIEW_FILE, hole=hole, pieces=pieces, question=QUESTION)
    saved = {key: value for key, value in plain_output(output).items() if key != "path"}
    (workspace / VIEW_FILE).write_text(json.dumps(saved, indent=1) + "\n", encoding="utf-8")
    return output


def find_fits(given: PuzzleInput, workspace: Path) -> FitsOutput:
    """The pinned reference: every piece that fills the hole; NanoAgent runs it out of the agent's sight."""
    return FitsOutput(pieces=_fits(_checked(given)))
