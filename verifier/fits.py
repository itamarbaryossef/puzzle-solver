"""find_fits, the task's reference, and the task itself: the agent's piece, placed in the hole as drawn."""

from .checks import TURNS, fits, flipped, hole, normal, piece_cells, puzzle_problem, result, turned, verify_puzzle


def verify_input(value):
    return verify_puzzle(value)


def verify_output(input_value, output_value, workspace):
    problem = puzzle_problem(input_value)
    if problem:
        return result(False, f"the puzzle is unusable: {problem}")
    if output_value.pieces != fits(input_value):
        return result(False, "the fits are not the puzzle's", fits=output_value.pieces, expected=fits(input_value))
    return result(True, "the fits follow from the puzzle", fits=output_value.pieces)


def name_key(name):
    """A name as compared: ignoring case and the spaces around it."""
    return name.strip().casefold()


def verify_task(arguments, output, reference, workspace):
    problem = puzzle_problem(arguments)
    if problem:
        return result(False, f"the puzzle is unusable: {problem}")
    if reference is None:
        return result(False, "there are no pinned fits to check against")
    expected = fits(arguments)
    if reference.pieces != expected:
        return result(False, "the pinned fits are not the puzzle's", fits=reference.pieces, expected=expected)
    if not name_key(output.piece):
        return result(False, "the answer names no piece", given=output.piece, expected=expected)
    pieces = {name_key(piece.name): piece for piece in arguments.pieces}
    piece = pieces.get(name_key(output.piece))
    if piece is None:
        return result(False, f"{output.piece!r} is not one of the pieces", given=output.piece, expected=expected)
    if piece.name not in expected:
        shape, target = piece_cells(piece), normal(hole(arguments))
        return result(
            False,
            f"piece {piece.name} does not fill the hole as drawn",
            given=output.piece,
            expected=expected,
            piece_cells=len(shape),
            hole_cells=len(target),
            fits_if_turned=any(turned(shape, turns) == target for turns in TURNS),
            fits_if_flipped=any(turned(flipped(shape), turns) == target for turns in TURNS),
        )
    return result(True, f"piece {piece.name} fills the hole", given=output.piece, expected=expected)
