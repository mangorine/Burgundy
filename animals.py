from enum import Enum

class AnimalType(Enum):
    CATTLE = "cattle"
    CHICKEN = "chicken"
    GOAT = "goat"
    PIG = "pig"
    SHEEP = "sheep"

class Animal:
    def __init__(self, type: AnimalType, quantity: int) -> None:
        self.type = type
        self.quantity = quantity