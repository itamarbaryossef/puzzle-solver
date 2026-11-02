"""view_puzzle: the view it returns is the one it saved, and it is the puzzle's hole and pieces, cell for cell."""

import json
from pathlib import Path

from .checks import FILLED, hole, normal, piece_cells, result, verify_puzzle

QUESTION = "Which piece fills the hole exactly, as drawn, without turning or flipping it?"


def verify_input(value):
    return verify_puzzle(value)


def verify_output(input_value, output_value, workspace):
    pieces = [{"name": piece.name, "cells": piece.cells} for piece in output_value.pieces]
    returned = {"hole": output_value.hole, "pieces": pieces, "question": output_value.question}
    path = Path(workspace) / output_value.path
    if not path.is_file() or json.loads(path.read_text(encoding="utf-8")) != returned:
        return result(False, "the returned view is not the one saved in the workspace", path=output_value.path)
    if output_value.question != QUESTION:
        return result(False, "the question is not the task's", question=output_value.question)
    if sorted(map(tuple, output_value.hole)) != sorted(hole(input_value)):
        return result(False, "the view's hole is not the picture's")
    if [piece.name for piece in output_value.pieces] != [piece.name for piece in input_value.pieces]:
        return result(False, "the view's pieces are not the puzzle's, in its order")
    for seen, piece in zip(output_value.pieces, input_value.pieces, strict=True):
        if sorted(map(tuple, seen.cells)) != sorted(normal(piece_cells(piece))):
            return result(False, f"the view's piece {piece.name} is not the '{FILLED}' cells drawn")
    return result(True, "the puzzle is viewed", path=output_value.path, hole=len(output_value.hole))
