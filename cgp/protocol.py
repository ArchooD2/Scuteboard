from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal

from model.tile import Tile


@dataclass(frozen=True)
class CgpMove:
    row: int
    column: int
    direction: Literal["horizontal", "vertical"]
    word: str


def parse_cgp_move(text: str) -> CgpMove:
    parts = text.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError("bad_move")

    square, word = parts
    if not word:
        raise ValueError("empty_word")

    horizontal = re.fullmatch(r"([A-Oa-o])([1-9]|1[0-5])", square)
    if horizontal is not None:
        column_text, row_text = horizontal.groups()
        return CgpMove(
            row=int(row_text) - 1,
            column=ord(column_text.upper()) - ord("A"),
            direction="horizontal",
            word=word,
        )

    vertical = re.fullmatch(r"([1-9]|1[0-5])([A-Oa-o])", square)
    if vertical is not None:
        row_text, column_text = vertical.groups()
        return CgpMove(
            row=int(row_text) - 1,
            column=ord(column_text.upper()) - ord("A"),
            direction="vertical",
            word=word,
        )

    raise ValueError("bad_square")


def format_tile_counts(tiles: list[Tile]) -> str:
    counts = Counter("?" if tile.is_blank else tile.letter.upper() for tile in tiles)
    symbols = [chr(ord("A") + index) for index in range(26)]
    symbols.append("?")
    return "".join(f"{counts[symbol]}{symbol}" for symbol in symbols if counts[symbol] > 0)
