from enum import Enum
from abc import ABC, abstractmethod
from typing import List, Optional


def castle_effect(player):
    """
    Castle: gives one action of any kind
    """
    player.turn += 1
    player.dice = [1, 2, 3, 4, 5, 6]


def mine_effect(player):
    """
    Mine: Gives one silverling at the end of the phase (on le call à la fin du coup)
    """
    player.silverlings += 1


def warehouse_effect(player):
    """
    Warehouse: Immediately allows the player to sell one good of their choice.
    """
    if not player.goods:
        return

    # Ici on laisse choisir le mec
    # Genre y'a une interface avec les tiles qui brillent ou whatever
    good_to_sell = player.choose("warehouse")  # là il choisit
    player.sell_good(good_to_sell)  # là ça vend


def workshop_effect(player, board):
    """
    Carpenter's Workshop: Takes the building tile of his choice (beige)
    """
    if not board.building or player.full:  # J'imagine un peu les attributs
        return

    building = player.choose("workshop")  # là il choisit
    player.personal_slots.append(building)


def church_effect(player, board):
    """
    Church: Takes the mine, knowledge or castle tile of his choice (c'est op wesh)
    """
    if not (board.castle and board.mine and board.knowledge) or player.full:
        return

    tile = player.choose("church")
    player.personal_slots.append(tile)


def market_effect(player, board):
    """
    Market: Allows the player to take any animal or ship.
    """
    if not (board.animal and board.ship) or player.full:
        return

    tile = player.choose("market")
    player.personal_slots.append(tile)


def house_effect(player):
    """
    Boarding House: Player takes 4 worker
    """
    player.workers += 4


def bank_effect(player):
    """
    Bank: Gain 2 silverlings
    """
    player.silverlings += 2


def cityhall_effect(player, game_state):
    """
    City Hall: Immediately place one additional yellow (knowledge) tile from your storage.
    """
    ...


def watchtower_effect(player, game_state):
    """
    Watchtower: Immediately score 4 victory points.
    """
    ...


class BuildingType(Enum):
    WAREHOUSE = "warehouse"
    WORKSHOP = "carpeter's workshop"
    CHURCH = "church"
    MARKET = "market"
    HOUSE = "boarding house"
    BANK = "bank"
    CITYHALL = "city hall"
    WATCHTOWER = "watchtower"


Effects = {
    BuildingType.WAREHOUSE: warehouse_effect,
    BuildingType.WORKSHOP: workshop_effect,
    BuildingType.CHURCH: church_effect,
    BuildingType.MARKET: market_effect,
    BuildingType.HOUSE: house_effect,
    BuildingType.BANK: bank_effect,
    BuildingType.CITYHALL: cityhall_effect,
    BuildingType.WATCHTOWER: watchtower_effect,
}


class Building:
    def __init__(self, type: BuildingType):
        self.type = type
        self.effect = Effects[type]
