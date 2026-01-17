from enum import Enum
from dataclasses import dataclass


class BuildingType(Enum):
    WAREHOUSE = "warehouse"
    WORKSHOP = "carpenter's workshop"
    CHURCH = "church"
    MARKET = "market"
    HOUSE = "boarding house"
    BANK = "bank"
    CITYHALL = "city hall"
    WATCHTOWER = "watchtower"


@dataclass(frozen=True)
class Building:
    building_type: BuildingType
