"""Checks shared by the tool verifiers. Pure functions of their arguments; they solve the puzzle on their own,
apart from src/plugin/puzzle.py, so a fault there cannot pass for an answer here."""

FILLED, EMPTY = "#", "."
SIDE = (2, 12)  # fewest and most rows, and columns, in the picture
HOLE = (3, 6)  # fewest and most cells in the hole
PIECES = (2, 4)  # fewest and most pieces
NAMES = "ABCD"
PIECE_SIDE = 4  # most rows, and columns, in a piece
PIECE_CELLS = (1, 8)  # fewest and most cells in a piece
TURNS = range(4)  # quarter turns, only to tell whether a wrong piece would fit turned


def result(valid, message, *, score=None, **details):
    return {
        "valid": valid,
        "score": float(valid) if score is None else score,
        "message": message,
        "details": details,
    }


def cells(rows, mark):
    return {(row, column) for row, line in enumerate(rows) for column, char in enumerate(line) if char == mark}


def normal(shape):
    """``shape`` moved so its top row and its left column are 0."""
    top = min(row for row, _ in shape)
    left = min(column for _, column in shape)
    return frozenset((row - top, column - left) for row, column in shape)


def turned(shape, turns):
    """``shape`` after ``turns`` clockwise quarter turns, each taking (row, column) to (column, -row): only to
    explain a wrong answer, since a piece is never turned."""
    for _ in range(turns):
        shape = [(column, -row) for row, column in shape]
    return normal(shape)


def flipped(shape):
    """``shape`` seen in a mirror, left and right swapped: only to explain a wrong answer."""
    return normal([(row, -column) for row, column in shape])


def joined(shape):
    """Whether every cell of ``shape`` reaches every other through cells sharing a side."""
    shape = set(shape)
    seen, todo = set(), [min(shape)]
    while todo:
        row, column = todo.pop()
        if (row, column) in seen:
            continue
        seen.add((row, column))
        for near in ((row - 1, column), (row + 1, column), (row, column - 1), (row, column + 1)):
            if near in shape:
                todo.append(near)
    return seen == shape


def hole(puzzle):
    return cells(puzzle.picture, EMPTY)


def piece_cells(piece):
    return cells(piece.rows, FILLED)


def fits(puzzle):
    """The name of every piece that fills the hole exactly as drawn, only moved, in the order given."""
    target = normal(hole(puzzle))
    return [piece.name for piece in puzzle.pieces if normal(piece_cells(piece)) == target]


def _drawing_problem(rows, what, fewest, most):
    if not fewest <= len(rows) <= most or not fewest <= len(rows[0]) <= most:
        return f"{what} must be {fewest} to {most} rows and columns"
    if any(len(row) != len(rows[0]) for row in rows):
        return f"{what}'s rows must all be the same length"
    if any(set(row) - {FILLED, EMPTY} for row in rows):
        return f"{what} may hold only '{FILLED}' and '{EMPTY}'"
    return None


def puzzle_problem(puzzle):
    """What makes ``puzzle`` not a puzzle with an answer, or None."""
    problem = _drawing_problem(puzzle.picture, "the picture", *SIDE)
    if problem:
        return problem
    empty = hole(puzzle)
    if not HOLE[0] <= len(empty) <= HOLE[1]:
        return f"the hole must be {HOLE[0]} to {HOLE[1]} cells, not {len(empty)}"
    if not joined(empty):
        return "the hole must be one piece: its cells joined side to side"
    if not PIECES[0] <= len(puzzle.pieces) <= PIECES[1]:
        return f"there must be {PIECES[0]} to {PIECES[1]} pieces, not {len(puzzle.pieces)}"
    names = [piece.name for piece in puzzle.pieces]
    if any(name not in NAMES for name in names) or len(set(names)) != len(names):
        return f"each piece must have its own name, one of {', '.join(NAMES)}"
    for piece in puzzle.pieces:
        problem = _drawing_problem(piece.rows, f"piece {piece.name}", 1, PIECE_SIDE)
        if problem:
            return problem
        if not PIECE_CELLS[0] <= len(piece_cells(piece)) <= PIECE_CELLS[1]:
            return f"piece {piece.name} must have {PIECE_CELLS[0]} to {PIECE_CELLS[1]} '{FILLED}' cells"
    if not fits(puzzle):
        return "no piece fills the hole"
    return None


def verify_puzzle(value):
    """verify_input of both tools: their input is the puzzle."""
    problem = puzzle_problem(value)
    if problem:
        return result(False, problem)
    return result(True, "input is valid")
