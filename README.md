# Burgundy

BOARD GAME : CASTLES OF BURGUNDY

# Rules of the game

Rules of the games here : [Rules](rules_burgundy.pdf)

# BOARD implementation choices + Tiles 

Géométrie Hexagonale et Grille : La représentation d'un plateau non rectangulaire avec 6 voisins par case a été résolue par l'utilisation de coordonnées axiales ($q, r$) plutôt qu'un tableau 2D standard. Plutôt qu'un tableau à deux dimensions (qui contiendrait beaucoup de "vide" vu la forme du plateau), la grille est stockée dans un dictionnaire self.grid: Dict[Tuple[int, int], Slot]. Cela permet de gérer facilement les trous dans la map ou des formes irrégulières. Cela simplifie aussi grandement le calcul des voisins, qui se fait par simple addition de vecteurs (ex: (1, 0), (1, -1), etc.)

Détection de Régions (Zoning) : Pour éviter de recalculer la connectivité des zones à chaque action, le code utilise une approche de pré-calcul. Un algorithme de "Flood Fill" est exécuté une seule fois à l'initialisation (_build_regions) pour générer des objets Region statiques, permettant de vérifier instantanément si une zone est complétée (is_completed). Les régions sont stockées sous forme d'objets Region contenant la liste de leurs slots. Lorsqu'on pose une tuile, on récupère simplement l'objet région associé via get_region_by_coord pour vérifier s'il est complet (is_completed()). C'est un choix d'optimisation efficace.

Gestion des Dépendances Circulaires : L'interdépendance entre le plateau (Board) et le joueur (Player) pour vérifier les règles est résolue par l'utilisation de if TYPE_CHECKING: et d'annotations par chaînes de caractères, permettant à l'analyseur statique de fonctionner sans provoquer d'erreurs d'importation à l'exécution.

# Player implementation

# Game implementation

# UI implementation