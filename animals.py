from enum import Enum

class Color(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    BLACK = "black"
    WHITE = "white"


class AnimalType(Enum):
    CATTLE = "cattle"
    CHICKEN = "chicken"
    GOAT = "goat"
    PIG = "pig"
    SHEEP = "sheep"


class Animal:
    def __init__(self, type: AnimalType, quantity: int, color: Color) -> None:
        self.type = type
        self.quantity = quantity
        self.color = color
