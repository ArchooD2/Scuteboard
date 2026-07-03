from dataclasses import dataclass
from typing import TypeAlias


@dataclass(frozen=True)
class SelectRackTile:
    tile_id: int


@dataclass(frozen=True)
class PlaceSelectedTile:
    row: int
    column: int


@dataclass(frozen=True)
class RecallTiles:
    pass


@dataclass(frozen=True)
class SubmitMove:
    pass


@dataclass(frozen=True)
class PassTurn:
    pass


@dataclass(frozen=True)
class SwapTiles:
    pass


@dataclass(frozen=True)
class NewGame:
    pass


@dataclass(frozen=True)
class FlipBoard:
    pass


@dataclass(frozen=True)
class ToggleCoordinates:
    pass


UIAction: TypeAlias = (
    SelectRackTile
    | PlaceSelectedTile
    | RecallTiles
    | SubmitMove
    | PassTurn
    | SwapTiles
    | NewGame
    | FlipBoard
    | ToggleCoordinates
)