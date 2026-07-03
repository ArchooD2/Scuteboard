from dataclasses import dataclass


@dataclass(frozen=True)
class Tile:
    id: int
    letter: str
    value: int
    is_blank: bool = False