from __future__ import annotations

import json
from pathlib import Path

from slimconfig import build_output, plain_output

import verifier
from contract import AnswerOutput, FitsOutput, PuzzleInput, ViewOutput
from plugin.puzzle import find_fits, view_puzzle

TASK = "find-the-piece"
INPUTS = Path(__file__).parent / "evals" / "inputs"


# The verifier gets contract instances, as NanoAgent's sandbox builds them from JSON.
def _puzzle(name: str) -> PuzzleInput:
    return build_output(json.loads((INPUTS / f"{name}.json").read_text()), PuzzleInput)


def _fits(puzzle: PuzzleInput, tmp_path: Path) -> dict:
    return plain_output(find_fits(puzzle, tmp_path))


def _check(piece: str, *, name: str = "04-mirror-trap", fits: dict | None = None, tmp_path: Path) -> dict:
    puzzle = _puzzle(name)
    fits = _fits(puzzle, tmp_path) if fits is None else fits
    output = build_output({"piece": piece}, AnswerOutput)
    return verifier.verify_task(TASK, puzzle, output, build_output(fits, FitsOutput), str(tmp_path))


def test_approves_the_tools_and_every_fitting_piece(tmp_path: Path) -> None:
    for path in sorted(INPUTS.glob("*.json")):
        puzzle = _puzzle(path.stem)
        viewed = build_output(plain_output(view_puzzle(puzzle, tmp_path)), ViewOutput)
        fits = _fits(puzzle, tmp_path)
        assert verifier.verify_input("view_puzzle", puzzle)["valid"] is True
        assert verifier.verify_output("view_puzzle", puzzle, viewed, str(tmp_path))["valid"] is True
        assert verifier.verify_output("find_fits", puzzle, build_output(fits, FitsOutput), str(tmp_path))["valid"]
        for piece in fits["pieces"]:
            verdict = _check(piece, name=path.stem, tmp_path=tmp_path)
            assert verdict["valid"] is True and verdict["score"] == 1.0, (path.stem, verdict)


def test_accepts_the_name_in_other_case_or_spacing(tmp_path: Path) -> None:
    assert _check(" c ", tmp_path=tmp_path)["valid"] is True


def test_accepts_either_piece_when_two_fit(tmp_path: Path) -> None:
    for piece, valid in [("A", True), ("D", True), ("B", False), ("C", False)]:
        assert _check(piece, name="10-two-pieces-fit", tmp_path=tmp_path)["valid"] is valid, piece


def test_refuses_a_mirror_image_and_says_it_would_fit_flipped(tmp_path: Path) -> None:
    verdict = _check("A", tmp_path=tmp_path)
    assert verdict["valid"] is False and verdict["score"] == 0.0 and "does not fill" in verdict["message"]
    assert (verdict["details"]["fits_if_flipped"], verdict["details"]["fits_if_turned"]) == (True, False)
    assert verdict["details"]["expected"] == ["C"]


def test_refuses_a_turned_copy_and_says_it_would_fit_turned(tmp_path: Path) -> None:
    verdict = _check("A", name="02-quarter-turn-trap", tmp_path=tmp_path)
    assert verdict["valid"] is False and verdict["details"]["fits_if_turned"] is True


def test_refuses_a_piece_a_cell_off_and_says_so(tmp_path: Path) -> None:
    verdict = _check("A", name="05-one-cell-extra", tmp_path=tmp_path)
    assert verdict["valid"] is False
    assert (verdict["details"]["fits_if_turned"], verdict["details"]["fits_if_flipped"]) == (False, False)
    assert (verdict["details"]["piece_cells"], verdict["details"]["hole_cells"]) == (6, 5)


def test_refuses_a_name_not_among_the_pieces(tmp_path: Path) -> None:
    for piece in ["D", "AB", "piece C", "1"]:
        verdict = _check(piece, tmp_path=tmp_path)
        assert verdict["valid"] is False and "not one of the pieces" in verdict["message"], piece
    assert "names no piece" in _check("  ", tmp_path=tmp_path)["message"]


def test_refuses_pinned_fits_that_do_not_follow_from_the_puzzle(tmp_path: Path) -> None:
    puzzle = _puzzle("04-mirror-trap")
    for broken in [{"pieces": ["A"]}, {"pieces": []}, {"pieces": ["C", "A"]}]:
        built = build_output(broken, FitsOutput)
        assert verifier.verify_output("find_fits", puzzle, built, str(tmp_path))["valid"] is False
        assert _check("A", fits=broken, tmp_path=tmp_path)["valid"] is False
        assert _check("C", fits=broken, tmp_path=tmp_path)["valid"] is False
    output = build_output({"piece": "C"}, AnswerOutput)
    assert verifier.verify_task(TASK, puzzle, output, None, str(tmp_path))["valid"] is False


def test_refuses_a_view_that_differs_from_the_puzzle_or_the_saved_file(tmp_path: Path) -> None:
    puzzle = _puzzle("04-mirror-trap")
    viewed = plain_output(view_puzzle(puzzle, tmp_path))
    moved = {**viewed, "hole": [[0, 0], *viewed["hole"][1:]]}
    for broken in [moved, {**viewed, "question": "Which piece is largest?"}]:
        verdict = verifier.verify_output("view_puzzle", puzzle, build_output(broken, ViewOutput), str(tmp_path))
        assert verdict["valid"] is False and "not the one saved" in verdict["message"]
    (tmp_path / viewed["path"]).unlink()
    assert (
        verifier.verify_output("view_puzzle", puzzle, build_output(viewed, ViewOutput), str(tmp_path))["valid"] is False
    )


def test_refuses_a_view_whose_saved_file_was_rewritten_to_match(tmp_path: Path) -> None:
    puzzle = _puzzle("04-mirror-trap")
    viewed = plain_output(view_puzzle(puzzle, tmp_path))
    moved = {**viewed, "hole": [[0, 0], *viewed["hole"][1:]]}
    (tmp_path / viewed["path"]).write_text(json.dumps({key: value for key, value in moved.items() if key != "path"}))
    verdict = verifier.verify_output("view_puzzle", puzzle, build_output(moved, ViewOutput), str(tmp_path))
    assert verdict["valid"] is False and "hole is not the picture's" in verdict["message"]


def test_refuses_a_puzzle_without_an_answer() -> None:
    puzzle = build_output(
        {"picture": ["####", "#..#", "#.##"], "pieces": [{"name": "A", "rows": ["###"]}, {"name": "B", "rows": ["#"]}]},
        PuzzleInput,
    )
    for tool in ["view_puzzle", "find_fits"]:
        verdict = verifier.verify_input(tool, puzzle)
        assert verdict["valid"] is False and "no piece fills" in verdict["message"]
