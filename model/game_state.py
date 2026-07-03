import random
from collections import Counter

from cgp.protocol import parse_cgp_move
from model.board_state import BoardState, PlacementMove, PlacedTile
from model.tile import Tile


class GameState:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.board: BoardState = BoardState()
        self.bag: list[Tile] = self._create_standard_bag()
        random.shuffle(self.bag)
        self.player_1_rack: list[Tile] = self._create_initial_rack(0)
        self.player_2_rack: list[Tile] = self._create_initial_rack(100)
        self.active_player_index: int = 0
        self.rack: list[Tile] = self.player_1_rack

        self.boardstate = self.board
        self.turn_number: int = 0
        self.player_1_score: int = 0
        self.player_2_score: int = 0

    def load_cgp_position(self, board_text: str, rack_text: str | None = None) -> None:
        self.board = BoardState.from_cgp_board(board_text)
        self.boardstate = self.board

        if rack_text is not None:
            self.set_rack_from_cgp(rack_text)

    def set_rack_from_cgp(self, rack_text: str) -> None:
        tiles: list[Tile] = []

        for index, character in enumerate(rack_text.strip()):
            tiles.append(
                Tile(
                    id=index,
                    letter=character.upper() if character != "?" else "?",
                    value=0 if character == "?" else 1,
                    is_blank=character == "?",
                )
            )

        self.player_1_rack = tiles
        if self.active_player_index == 0:
            self.rack = self.player_1_rack

    def cgp_board(self) -> str:
        return self.board.to_cgp_board()

    def cgp_rack(self) -> str:
        return "".join("?" if tile.is_blank else tile.letter.upper() for tile in self.rack)

    def current_player_name(self) -> str:
        return f"Player {self.active_player_index + 1}"

    def active_player_rack(self) -> list[Tile]:
        return self.player_1_rack if self.active_player_index == 0 else self.player_2_rack

    def switch_turn(self) -> None:
        self.active_player_index = 1 - self.active_player_index
        self.rack = self.active_player_rack()

    def _next_tile_id(self) -> int:
        used_ids = [tile.id for tile in self.bag]
        used_ids.extend(tile.id for tile in self.player_1_rack)
        used_ids.extend(tile.id for tile in self.player_2_rack)
        used_ids.extend(
            placed_tile.tile.id
            for placed_tile in self.board.pending_tiles()
        )
        used_ids.extend(
            placed_tile.tile.id
            for row in self.board._cells
            for placed_tile in row
            if placed_tile is not None
        )

        if not used_ids:
            return 0

        return max(used_ids) + 1

    def _create_standard_bag(self) -> list[Tile]:
        distribution = {
            "A": (9, 1),
            "B": (2, 3),
            "C": (2, 3),
            "D": (4, 2),
            "E": (12, 1),
            "F": (2, 4),
            "G": (3, 2),
            "H": (2, 4),
            "I": (9, 1),
            "J": (1, 8),
            "K": (1, 5),
            "L": (4, 1),
            "M": (2, 3),
            "N": (6, 1),
            "O": (8, 1),
            "P": (2, 3),
            "Q": (1, 10),
            "R": (6, 1),
            "S": (4, 1),
            "T": (6, 1),
            "U": (4, 1),
            "V": (2, 4),
            "W": (2, 4),
            "X": (1, 8),
            "Y": (2, 4),
            "Z": (1, 10),
            "?": (2, 0),
        }

        tiles: list[Tile] = []
        next_id = 0
        for letter, (count, value) in distribution.items():
            for _ in range(count):
                tiles.append(
                    Tile(
                        id=next_id,
                        letter=letter,
                        value=value,
                        is_blank=letter == "?",
                    )
                )
                next_id += 1

        return tiles

    def _draw_tiles(self, count: int, id_offset: int) -> list[Tile]:
        tiles: list[Tile] = []
        for _ in range(min(count, len(self.bag))):
            tile = self.bag.pop(0)
            tiles.append(
                Tile(
                    id=tile.id + id_offset,
                    letter=tile.letter,
                    value=tile.value,
                    is_blank=tile.is_blank,
                )
            )
        return tiles

    def staged_tile_at(self, row: int, column: int) -> PlacedTile | None:
        return self.board.tile_at(row, column)

    def stage_tile(self, tile_id: int, row: int, column: int) -> bool:
        if self.board.tile_at(row, column) is not None:
            return False

        tile = self.rack_tile_by_id(tile_id)
        if tile is None:
            return False

        self.rack.remove(tile)
        self.board.place(
            PlacedTile(
                tile=tile,
                row=row,
                column=column,
                committed=False,
            )
        )
        return True

    def recall_pending_tiles(self) -> None:
        tiles = self.board.clear_pending()
        self.rack.extend(placed_tile.tile for placed_tile in tiles)

    def _active_rack_refill(self) -> None:
        needed = max(0, 7 - len(self.rack))
        self.rack.extend(self._draw_tiles(needed, self._next_tile_id()))

    def submit_turn(self) -> str | None:
        pending = self.board.pending_tiles()
        if not pending:
            return "no_move"

        rows = {placed_tile.row for placed_tile in pending}
        columns = {placed_tile.column for placed_tile in pending}

        if len(rows) > 1 and len(columns) > 1:
            return "not_in_line"

        if len(rows) == 1:
            row = next(iter(rows))
            columns_sorted = sorted(columns)
            start_column = columns_sorted[0]
            end_column = columns_sorted[-1]
            letters: list[str] = []

            for column in range(start_column, end_column + 1):
                placed_tile = self.board.tile_at(row, column)
                if placed_tile is None:
                    return "gapped_word"
                letters.append(placed_tile.tile.letter)

            move = PlacementMove(row=row, column=start_column, direction="horizontal", word="".join(letters))
        else:
            column = next(iter(columns))
            rows_sorted = sorted(rows)
            start_row = rows_sorted[0]
            end_row = rows_sorted[-1]
            letters = []

            for row in range(start_row, end_row + 1):
                placed_tile = self.board.tile_at(row, column)
                if placed_tile is None:
                    return "gapped_word"
                letters.append(placed_tile.tile.letter)

            move = PlacementMove(row=start_row, column=column, direction="vertical", word="".join(letters))

        validation_rack = self.rack + [placed_tile.tile for placed_tile in pending]
        validation_board = self.board.copy()
        validation_board.clear_pending()
        error = validation_board.validate_move(move, validation_rack)
        if error is not None:
            return error

        self.board.commit_pending()
        self._active_rack_refill()
        self.turn_number += 1
        self.switch_turn()
        return None

    def pass_turn(self) -> None:
        self.recall_pending_tiles()
        self.turn_number += 1
        self.switch_turn()

    def swap_turn(self) -> bool:
        self.recall_pending_tiles()

        if not self.bag:
            return False

        current_rack = self.rack[:]
        self.rack.clear()
        self.bag.extend(current_rack)

        self._active_rack_refill()
        self.turn_number += 1
        self.switch_turn()
        return True

    def play_cgp_bestmove(self, bestmove: str) -> str | None:
        text = bestmove.strip()
        if text.lower() == "pass":
            self.pass_turn()
            return None

        if text.lower().startswith("exchange "):
            return None if self.swap_turn() else "swap_unavailable"

        try:
            move = parse_cgp_move(text)
        except ValueError as error:
            return str(error)

        placement = PlacementMove(
            row=move.row,
            column=move.column,
            direction=move.direction,
            word=move.word,
        )
        error = self.board.validate_move(placement, self.rack)
        if error is not None:
            return error

        self.recall_pending_tiles()
        step_row, step_column = (0, 1) if move.direction == "horizontal" else (1, 0)

        for offset, raw_letter in enumerate(move.word):
            row = move.row + step_row * offset
            column = move.column + step_column * offset
            if self.board.tile_at(row, column) is not None:
                continue

            tile = self._take_rack_tile(raw_letter)
            if tile is None:
                return f"missing_tile_{raw_letter.upper()}"

            self.board.place(
                PlacedTile(
                    tile=tile,
                    row=row,
                    column=column,
                    committed=False,
                )
            )

        self.board.commit_pending()
        self._active_rack_refill()
        self.turn_number += 1
        self.switch_turn()
        return None

    def _take_rack_tile(self, raw_letter: str) -> Tile | None:
        if raw_letter.islower():
            for tile in self.rack:
                if tile.is_blank:
                    self.rack.remove(tile)
                    return Tile(
                        id=tile.id,
                        letter=raw_letter.upper(),
                        value=0,
                        is_blank=True,
                    )
            return None

        target = raw_letter.upper()
        for tile in self.rack:
            if not tile.is_blank and tile.letter.upper() == target:
                self.rack.remove(tile)
                return tile

        for tile in self.rack:
            if tile.is_blank:
                self.rack.remove(tile)
                return Tile(
                    id=tile.id,
                    letter=target,
                    value=0,
                    is_blank=True,
                )

        return None

    def validate_placement(self, tile_id: int, row: int, column: int) -> str | None:
        tile = self.rack_tile_by_id(tile_id)
        if tile is None:
            return "missing_tile"

        move = PlacementMove(
            row=row,
            column=column,
            direction="horizontal",
            word=tile.letter,
        )

        return self.board.validate_move(move, self.rack)

    def rack_tile_by_id(self, tile_id: int) -> Tile | None:
        for tile in self.rack:
            if tile.id == tile_id:
                return tile

        return None

    def place_rack_tile(
        self,
        tile_id: int,
        row: int,
        column: int,
    ) -> bool:
        return self.stage_tile(tile_id, row, column)

    def _create_initial_rack(self, id_offset: int) -> list[Tile]:
        rack = self._draw_tiles(7, id_offset)
        if len(rack) < 7:
            fallback_letters = ["A", "E", "I", "N", "R", "S", "T"]
            fallback_values = [1, 1, 1, 1, 1, 1, 1]
            start_index = len(rack)
            for index, (letter, value) in enumerate(zip(fallback_letters[start_index:], fallback_values[start_index:], strict=True), start=start_index):
                rack.append(
                    Tile(id=id_offset + index, letter=letter, value=value)
                )
        return rack

