# Burgundy

BOARD GAME : CASTLES OF BURGUNDY

# Rules of the game

Rules of the games here : [Rules](rules_burgundy.pdf)

# BOARD implementation choices + Tiles 

Géométrie Hexagonale et Grille : La représentation d'un plateau non rectangulaire avec 6 voisins par case a été résolue par l'utilisation de coordonnées axiales ($q, r$) plutôt qu'un tableau 2D standard. Plutôt qu'un tableau à deux dimensions (qui contiendrait beaucoup de "vide" vu la forme du plateau), la grille est stockée dans un dictionnaire self.grid: Dict[Tuple[int, int], Slot]. Cela permet de gérer facilement les trous dans la map ou des formes irrégulières. Cela simplifie aussi grandement le calcul des voisins, qui se fait par simple addition de vecteurs (ex: (1, 0), (1, -1), etc.)

Détection de Régions (Zoning) : Pour éviter de recalculer la connectivité des zones à chaque action, le code utilise une approche de pré-calcul. Un algorithme de "Flood Fill" est exécuté une seule fois à l'initialisation (_build_regions) pour générer des objets Region statiques, permettant de vérifier instantanément si une zone est complétée (is_completed). Les régions sont stockées sous forme d'objets Region contenant la liste de leurs slots. Lorsqu'on pose une tuile, on récupère simplement l'objet région associé via get_region_by_coord pour vérifier s'il est complet (is_completed()). C'est un choix d'optimisation efficace.

Gestion des Dépendances Circulaires : L'interdépendance entre le plateau (Board) et le joueur (Player) pour vérifier les règles est résolue par l'utilisation de if TYPE_CHECKING: et d'annotations par chaînes de caractères, permettant à l'analyseur statique de fonctionner sans provoquer d'erreurs d'importation à l'exécution.

Tuiles Jaunes : Elles introduisent des exceptions aux règles (revenus, modifications de placement, score de fin de partie). Une classe de base YellowTile se divise en trois sous-classes immuables :
Income : Pour les gains de ressources.
RuleModification : Pour les changements de règles de jeu.
Scoring : Pour les points de victoire en fin de partie.
Pour les RuleModification (modifications de règles), le code ne peut pas deviner comment altérer le flux du jeu. Le moteur doit vérifier explicitement la présence de ces pouvoirs. Par exemple, lorsqu'on vérifie si une tuile bâtiment peut être posée (can_place_tile_at), le code contient une "béquille" spécifique pour la tuile jaune, c'est la méthode de placement qui demande "Est-ce que l'exception X est active ?". (NB:  en gros c'est hardcode dans le jue, au lieu de creer une fonction en plus on modifie carrement une fonction a un niveau plus bas d'abstraction)

# Player implementation

# Game implementation

# UI implementation