from __future__ import annotations

import json
from pathlib import Path

import pytest
from slimconfig import build_output, plain_output

import verifier.checks
from contract import PuzzleInput
from plugin.puzzle import VIEW_FILE, cells, find_fits, puzzle_problem, trim, view_puzzle

INPUTS = Path(__file__).parent / "evals" / "inputs"
# Every eval puzzle's fits, worked out by hand: its file name says which case it is.
EXPECTED = {
    "01-small-hole": ["B"],
    "02-quarter-turn-trap": ["B"],
    "03-half-turn-trap": ["A"],
    "04-mirror-trap": ["C"],
    "05-one-cell-extra": ["B"],
    "06-one-cell-missing": ["C"],
    "07-padded-piece": ["A"],
    "08-hole-on-edge": ["B"],
    "09-plus-hole": ["B"],
    "10-two-pieces-fit": ["A", "D"],
    "11-two-pieces": ["B"],
    "12-six-cells": ["C"],
    "13-four-pieces": ["C"],
    "14-large-picture": ["D"],
    "15-all-traps": ["B"],
}
L_PIECE = ["#.", "#.", "##"]


def _puzzle(name: str) -> PuzzleInput:
    return build_output(json.loads((INPUTS / f"{name}.json").read_text()), PuzzleInput)


def _with(name: str, **changes) -> PuzzleInput:
    return build_output({**plain_output(_puzzle(name)), **changes}, PuzzleInput)


def test_a_piece_is_only_moved_never_turned_or_flipped(tmp_path: Path) -> None:
    picture = ["#####", "#.###", "#.###", "#..##", "#####"]  # an upright L
    pieces = [
        {"name": "A", "rows": ["###", "#.."]},  # the L turned a quarter
        {"name": "B", "rows": [".#", ".#", "##"]},  # its mirror image
        {"name": "C", "rows": ["#.", "#.", "##"]},  # the L as drawn
    ]
    puzzle = build_output({"picture": picture, "pieces": pieces}, PuzzleInput)
    assert find_fits(puzzle, tmp_path).pieces == ["C"]


def test_a_blank_border_is_trimmed() -> None:
    assert trim(cells(["....", ".#..", ".##.", "...."], "#")) == trim(cells(["#.", "##"], "#"))


def test_every_eval_puzzle_has_its_intended_fits(tmp_path: Path) -> None:
    assert sorted(path.stem for path in INPUTS.glob("*.json")) == sorted(EXPECTED)
    for name, expected in EXPECTED.items():
        puzzle = _puzzle(name)
        assert puzzle_problem(puzzle) is None, name
        assert find_fits(puzzle, tmp_path).pieces == expected == verifier.checks.fits(puzzle), name


def test_the_view_is_the_hole_and_the_trimmed_pieces(tmp_path: Path) -> None:
    viewed = view_puzzle(_puzzle("07-padded-piece"), tmp_path)
    assert viewed.hole == [[1, 3], [2, 2], [2, 3], [2, 4]]
    assert viewed.pieces[0].cells == [[0, 1], [1, 0], [1, 1], [1, 2]]
    saved = json.loads((tmp_path / VIEW_FILE).read_text())
    assert saved == {key: value for key, value in plain_output(viewed).items() if key != "path"}


@pytest.mark.parametrize(
    ("changes", "problem"),
    [
        ({"picture": ["####", "#..", "####"]}, "same length"),
        ({"picture": ["####", "#..#", "#.x#"]}, "only"),
        ({"picture": ["#" * 13] * 3}, "rows and columns"),
        ({"picture": ["####", "#..#", "####"]}, "the hole must be 3 to 6 cells"),
        ({"picture": ["#####", "#...#", "#...#", "##.##"]}, "the hole must be 3 to 6 cells"),
        ({"picture": ["#####", "#.#.#", "#.###"]}, "one piece"),
        ({"pieces": [{"name": "A", "rows": L_PIECE}]}, "2 to 4 pieces"),
        ({"pieces": [{"name": name, "rows": L_PIECE} for name in "ABCDA"]}, "2 to 4 pieces"),
        ({"pieces": [{"name": "A", "rows": L_PIECE}, {"name": "E", "rows": L_PIECE}]}, "own name"),
        ({"pieces": [{"name": "A", "rows": L_PIECE}, {"name": "A", "rows": L_PIECE}]}, "own name"),
        ({"pieces": [{"name": "A", "rows": L_PIECE}, {"name": "B", "rows": ["#####"]}]}, "rows and columns"),
        ({"pieces": [{"name": "A", "rows": L_PIECE}, {"name": "B", "rows": ["..", ".."]}]}, "cells"),
        ({"pieces": [{"name": "A", "rows": ["###"]}, {"name": "B", "rows": ["##", "##"]}]}, "no piece fills"),
    ],
)
def test_refuses_a_puzzle_without_an_answer(changes: dict, problem: str, tmp_path: Path) -> None:
    puzzle = _with("01-small-hole", **changes)
    assert problem in (puzzle_problem(puzzle) or "")
    assert problem in (verifier.checks.puzzle_problem(puzzle) or "")
    with pytest.raises(ValueError, match=problem):
        view_puzzle(puzzle, tmp_path)
    with pytest.raises(ValueError, match=problem):
        find_fits(puzzle, tmp_path)
