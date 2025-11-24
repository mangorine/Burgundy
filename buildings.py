from enum import Enum
from abc import ABC, abstractmethod

class BuildingType(Enum):
    CASTLE = "castle"
    MINE = "mine"
    WAREHOUSE = "warehouse"
    WORKSHOP = "carpeter's workshop"
    CHURCH = "church"
    MARKET = "market"
    HOUSE = "boarding house"
    BANK = "bank"
    CITYHALL = "city hall"
    WATCHTOWER = "watchtower"

class Building:
    def __init__(self, name, color=None, description="", on_place=None, on_phase_end=None, immediate_action=False):
        self.color = color
        self.name = name
        self.description = description
        self.on_place = on_place
        self.on_phase_end = on_phase_end
        self.immediate_action = immediate_action

    def trigger_on_place(self, player, game_state):
        if self.on_place:
            self.on_place(player, game_state)

    def trigger_on_phase_end(self, player, game_state):
        if self.on_phase_end:
            self.on_phase_end(player, game_state)

    

def castle_effect(player):
    """
    Castle: gives one action of any kind
    """
    player.turn +=1
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
    player.sell_good(good_to_sell)               # là ça vend

def workshop_effect(player, board):
    """
    Carpenter's Workshop: Takes the building tile of his choice (beige)
    """
    if not board.building or player.full:           # J'imagine un peu les attributs
        return
    
    building = player.choose("workshop")     # là il choisit
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

BUILDINGS = {
    "CASTLE": Building(
        name="Castle",
        description="gives one action of any kind",
        on_place=castle_effect,
        immediate_action=True
    ),
    "MINE": Building(
        name="Mine",
        description="Gives one silverling at the end of the phase (on le call à la fin du coup)",
        on_phase_end=mine_effect
    ),
    "WAREHOUSE": Building(
        name="Warehouse",
        description="Immediately allows the player to sell one good of their choice.",
        on_place=warehouse_effect,
        immediate_action=True
    ),
    "WORKSHOP": Building(
        name="Carpenter's Workshop",
        description="Takes the building tile of his choice (beige)",
        on_place=workshop_effect,
        immediate_action=True,
    ),
    "CHURCH": Building(
        name="Church",
        description="Takes the mine, knowledge or castle tile of his choice (c'est op wesh)",
        on_place=church_effect,
        immediate_action=True,
    ),
    "MARKET": Building(
        name="Market",
        description="Allows the player to take any animal or ship.",
        on_place=market_effect,
        immediate_action=True,
    ),
    "HOUSE": Building(
        name="Boarding House",
        description="Player takes 4 worker tiles",
        on_place=house_effect,
        immediate_action=True,
    ),
    "BANK": Building(
        name="Bank",
        description="Gain 2 silverlings",
        on_place=bank_effect,
        immediate_action=True,
    ),
    "CITYHALL": Building(
        name="City Hall",
        description="Immediately place one additional yellow (knowledge) tile from your storage.",
        on_place=cityhall_effect,
        immediate_action=True,
    ),
    "WATCHTOWER": Building(
        name="Watchtower",
        description="Immediately score 4 victory points.",
        on_place=watchtower_effect,
        immediate_action=True,
    ),
}
