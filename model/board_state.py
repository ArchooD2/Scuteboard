from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal, Sequence

from model.tile import Tile


@dataclass(frozen=True)
class PlacedTile:
    tile: Tile
    row: int
    column: int
    committed: bool


@dataclass(frozen=True)
class PlacementMove:
    row: int
    column: int
    direction: Literal["horizontal", "vertical"]
    word: str


class BoardState:
    SIZE = 15
    STANDARD_PREMIUMS: tuple[tuple[str | None, ...], ...] = (
        ("TW", None, None, "DL", None, None, None, "TW", None, None, None, "DL", None, None, "TW"),
        (None, "DW", None, None, None, "TL", None, None, None, "TL", None, None, None, "DW", None),
        (None, None, "DW", None, None, None, "DL", None, "DL", None, None, None, "DW", None, None),
        ("DL", None, None, "DW", None, None, None, "DL", None, None, None, "DW", None, None, "DL"),
        (None, None, None, None, "DW", None, None, None, None, None, "DW", None, None, None, None),
        (None, "TL", None, None, None, "TL", None, None, None, "TL", None, None, None, "TL", None),
        (None, None, "DL", None, None, None, "DL", None, "DL", None, None, None, "DL", None, None),
        ("TW", None, None, "DL", None, None, None, "DW", None, None, None, "DL", None, None, "TW"),
        (None, None, "DL", None, None, None, "DL", None, "DL", None, None, None, "DL", None, None),
        (None, "TL", None, None, None, "TL", None, None, None, "TL", None, None, None, "TL", None),
        (None, None, None, None, "DW", None, None, None, None, None, "DW", None, None, None, None),
        ("DL", None, None, "DW", None, None, None, "DL", None, None, None, "DW", None, None, "DL"),
        (None, None, "DW", None, None, None, "DL", None, "DL", None, None, None, "DW", None, None),
        (None, "DW", None, None, None, "TL", None, None, None, "TL", None, None, None, "DW", None),
        ("TW", None, None, "DL", None, None, None, "TW", None, None, None, "DL", None, None, "TW"),
    )

    def __init__(self) -> None:
        self._cells: list[list[PlacedTile | None]] = [
            [None for _ in range(self.SIZE)]
            for _ in range(self.SIZE)
        ]

    def premium_at(self, row: int, column: int) -> str | None:
        if not self.is_in_bounds(row, column):
            return None

        return self.STANDARD_PREMIUMS[row][column]

    def is_in_bounds(self, row: int, column: int) -> bool:
        return 0 <= row < self.SIZE and 0 <= column < self.SIZE

    def tile_at(self, row: int, column: int) -> PlacedTile | None:
        if not self.is_in_bounds(row, column):
            return None

        return self._cells[row][column]

    def has_committed_tiles(self) -> bool:
        for row in self._cells:
            for placed_tile in row:
                if placed_tile is not None and placed_tile.committed:
                    return True

        return False

    def pending_tiles(self) -> list[PlacedTile]:
        tiles: list[PlacedTile] = []

        for row in self._cells:
            for placed_tile in row:
                if placed_tile is not None and not placed_tile.committed:
                    tiles.append(placed_tile)

        return tiles

    def copy(self) -> BoardState:
        board = BoardState()
        for row_index, row in enumerate(self._cells):
            for column_index, placed_tile in enumerate(row):
                if placed_tile is None:
                    continue

                board._cells[row_index][column_index] = PlacedTile(
                    tile=placed_tile.tile,
                    row=placed_tile.row,
                    column=placed_tile.column,
                    committed=placed_tile.committed,
                )

        return board

    def clear_pending(self) -> list[PlacedTile]:
        tiles = self.pending_tiles()

        for placed_tile in tiles:
            self._cells[placed_tile.row][placed_tile.column] = None

        return tiles

    def commit_pending(self) -> None:
        for row_index, row in enumerate(self._cells):
            for column_index, placed_tile in enumerate(row):
                if placed_tile is None or placed_tile.committed:
                    continue

                self._cells[row_index][column_index] = PlacedTile(
                    tile=placed_tile.tile,
                    row=placed_tile.row,
                    column=placed_tile.column,
                    committed=True,
                )

    def validate_move(
        self,
        move: PlacementMove,
        rack: Sequence[Tile],
    ) -> str | None:
        word = move.word.strip()
        if not word:
            return "empty_word"

        step_row, step_column = (0, 1) if move.direction == "horizontal" else (1, 0)
        end_row = move.row + step_row * (len(word) - 1)
        end_column = move.column + step_column * (len(word) - 1)

        if not self.is_in_bounds(move.row, move.column) or not self.is_in_bounds(end_row, end_column):
            return "out_of_bounds"

        rack_letters = Counter(tile.letter.upper() for tile in rack if not tile.is_blank)
        blank_count = sum(1 for tile in rack if tile.is_blank)
        new_tiles_needed = 0

        for offset, raw_letter in enumerate(word):
            row = move.row + step_row * offset
            column = move.column + step_column * offset
            existing_tile = self.tile_at(row, column)
            target_letter = raw_letter.upper()

            if existing_tile is not None:
                if existing_tile.tile.letter.upper() != target_letter:
                    return f"conflict_at_{row}_{column}"
                continue

            new_tiles_needed += 1

            if raw_letter.islower():
                if blank_count <= 0:
                    return "missing_blank_tile"
                blank_count -= 1
                continue

            if rack_letters[target_letter] > 0:
                rack_letters[target_letter] -= 1
                continue

            if blank_count > 0:
                blank_count -= 1
                continue

            return f"missing_tile_{target_letter}"

        if new_tiles_needed == 0:
            return "no_new_tiles"

        if not self.has_committed_tiles():
            center = self.SIZE // 2
            covers_center = False
            for offset in range(len(word)):
                row = move.row + step_row * offset
                column = move.column + step_column * offset
                if row == center and column == center:
                    covers_center = True
                    break

            if not covers_center:
                return "must_cover_center"

        return None

    def place(self, placed_tile: PlacedTile) -> None:
        if not self.is_in_bounds(placed_tile.row, placed_tile.column):
            raise ValueError("out_of_bounds")

        if self._cells[placed_tile.row][placed_tile.column] is not None:
            raise ValueError("occupied")

        self._cells[placed_tile.row][placed_tile.column] = placed_tile

    def remove(self, row: int, column: int) -> PlacedTile | None:
        if not self.is_in_bounds(row, column):
            return None

        tile = self._cells[row][column]
        self._cells[row][column] = None
        return tile

    def to_cgp_board(self) -> str:
        rows: list[str] = []

        for row in self._cells:
            encoded_row: list[str] = []
            empty_run = 0

            for placed_tile in row:
                if placed_tile is None:
                    empty_run += 1
                    continue

                if empty_run > 0:
                    encoded_row.append(str(empty_run))
                    empty_run = 0

                letter = placed_tile.tile.letter.lower() if placed_tile.tile.is_blank else placed_tile.tile.letter.upper()
                encoded_row.append(letter)

            if empty_run > 0:
                encoded_row.append(str(empty_run))

            rows.append("".join(encoded_row) or "15")

        return "/".join(rows)

    @classmethod
    def from_cgp_board(cls, board_text: str) -> BoardState:
        board = cls()
        rows = board_text.split("/")

        if len(rows) != cls.SIZE:
            raise ValueError("bad_position")

        for row_index, row_text in enumerate(rows):
            column = 0
            index = 0

            while index < len(row_text):
                character = row_text[index]

                if character.isdigit():
                    run_end = index + 1
                    while run_end < len(row_text) and row_text[run_end].isdigit():
                        run_end += 1

                    column += int(row_text[index:run_end])
                    index = run_end
                    continue

                if column >= cls.SIZE:
                    raise ValueError("bad_position")

                tile = Tile(
                    id=-(row_index * cls.SIZE + column + 1),
                    letter=character.upper(),
                    value=0,
                    is_blank=character.islower(),
                )
                board._cells[row_index][column] = PlacedTile(
                    tile=tile,
                    row=row_index,
                    column=column,
                    committed=True,
                )
                column += 1
                index += 1

            if column != cls.SIZE:
                raise ValueError("bad_position")

        return board