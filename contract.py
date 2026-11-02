"""Each tool's and task's typed input and output (see nanoagent.plugin.v0001.contract): declarations only."""

from dataclasses import dataclass
from enum import Enum
from typing import Annotated

from slimconfig import Output


class Tool(Enum):
    VIEW_PUZZLE = "view_puzzle"
    FIND_FITS = "find_fits"


class Task(Enum):
    FIND_THE_PIECE = "find-the-piece"


@dataclass
class Piece(Output):
    name: Annotated[str, "The piece's label: one letter from A to D"]
    rows: Annotated[list[str], "The piece drawn row by row, top to bottom: '#' is part of the piece, '.' is empty"]


@dataclass
class PuzzleInput(Output):
    picture: Annotated[
        list[str], "The picture drawn row by row, top to bottom: '#' is filled, '.' is the hole, one connected region"
    ]
    pieces: Annotated[list[Piece], "The candidate pieces, 2 to 4 of them"]


@dataclass
class PieceCells(Output):
    name: Annotated[str, "The piece's label"]
    cells: Annotated[
        list[list[int]], "The piece's cells as [row, column], trimmed so its top row and left column are 0"
    ]


@dataclass
class ViewOutput(Output):
    path: Annotated[str, "The view's JSON file, relative to the workspace"]
    hole: Annotated[list[list[int]], "The hole's cells as [row, column] in the picture; row 0 is the top"]
    pieces: Annotated[list[PieceCells], "Each piece's cells, in the order given"]
    question: Annotated[str, "The question to answer about the picture"]


@dataclass
class FitsOutput(Output):
    pieces: Annotated[list[str], "The label of every piece that fills the hole exactly as drawn, in the order given"]


@dataclass
class AnswerOutput(Output):
    piece: Annotated[str, "The label of a piece that fills the hole exactly as drawn, without turning or flipping it"]


TOOLS = {
    Tool.VIEW_PUZZLE: (PuzzleInput, ViewOutput),
    Tool.FIND_FITS: (PuzzleInput, FitsOutput),
}
TASKS = {Task.FIND_THE_PIECE: (PuzzleInput, AnswerOutput)}
