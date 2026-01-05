from enum import Enum
from dataclasses import dataclass
from typing import Any, Dict

class ActionType(Enum):
    TRADE_DIE = "trade die"
    SELL_GOOD = "sell good"
    TAKE_TILE = "take a tile"
    BUY_TILE = "buy a tile"
    PLACE_TILE = "place a tile"
    CHANGE_DIE_VALUE = "change a die value"
    DISCARD_TILE = "discard a tile"

@dataclass(frozen=True)
class Action:
    type: ActionType
    params: Dict[str, Any]
    cost: Dict[str, int] = None