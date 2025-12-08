from dataclasses import dataclass
from enum import Enum, auto


class AnimalType(Enum):
    """
    Types d'animaux possibles sur les tuiles vertes.

    """

    SHEEP = auto()
    PIG = auto()
    CATTLE = auto()
    CHICKEN = auto()
    GOAT = auto()


@dataclass(frozen=True)
class Animal:
    """
    Représente une tuile Animal.
    """

    animal_type: AnimalType
    count: int = 1  # valeur par défaut

    def score_within_region(self, same_type_tiles_in_region: int) -> int:
        """
        Calcule le score fourni par cette tuile dans une région donnée.
        """
        if same_type_tiles_in_region <= 0:
            return 0
        return self.count * same_type_tiles_in_region
