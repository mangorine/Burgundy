from enum import Enum

class Action(Enum):
    TRADE_DIE = "trade die"
    SELL_GOOD = "sell good"
    TAKE_TILE = "take a tile"
    BUY_TILE = "buy a tile"
    PLACE_TILE = "place a tile"
    CHANGE_DIE_VALUE = "change a die value"
    DISCARD_TILE = "discard a tile"
    
