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

Gestion Centralisée des Ressources et États : L'utilisation d'une @dataclass réduit le code superflu tout en garantissant l'intégrité des données. La classe impose l'usage de méthodes transactionnelles (spend_workers, etc.) qui encapsulent la validation directement dans le modèle. Cela empêche l'existence d'états invalides (comme un nombre négatif d'ouvriers) indépendamment de la complexité de l'interface ou de l'IA appelante.

Stockage Tuiles et Marchandises : La classe distingue deux logiques de stockage. Pour les tuiles, une limite stricte de quantité est appliquée. Pour les marchandises, la limite porte sur la variété (max 3 types) et non la quantité. L'utilisation d'un simple Set pour vérifier l'unicité des couleurs en O(n) remplace avantageusement des structures complexes, simplifiant la gestion et la sérialisation de l'état.

Mécanique Modulaire des Dés : La modification des dés est traitée comme un problème de distance cyclique. L'algorithme calcule instantanément (O(1)) la distance minimale bidirectionnelle (horaire et anti-horaire) via l'arithmétique modulaire. Cela rend la vérification de faisabilité immédiate, même avec des coûts variables ou des modificateurs de règles.

Centralisation des Règles Spéciales : La classe Player agit comme un adaptateur pour les Tuiles Jaunes. Plutôt que de laisser le moteur vérifier la présence de tuiles spécifiques, il interroge le joueur sur ses capacités (ex: get_die_adjustment_per_worker). Cette abstraction centralise les exceptions dans l'objet joueur, évitant de polluer le moteur principal avec des vérifications conditionnelles.

Pré-calcul de l'Espace d'Action : La classe expose l'espace d'action complet via des méthodes de pré-calcul (get_valid_placement_coords). En croisant l'état du plateau et des dés, elle fournit directement la liste des coups légaux et leur coût exact. Cela décharge le contrôleur (IA ou UI) de la complexité des règles de validation.

# Game implementation

Validation Transactionnelle : La méthode centrale action_place_tile_from_storage applique un modèle de sécurité atomique. Toutes les contraintes (dés, topologie, coûts) sont validées avant la moindre modification d'état. Cette approche prévient la corruption des données en garantissant qu'aucune ressource n'est consommée pour une action qui serait finalement illégale.

Injection de Contexte et Découplage UI : L'argument extra_context permet de gérer les choix utilisateur (ex: quel dépôt vider) sans interrompre le flux d'exécution. Ce dictionnaire permet à l'interface de pré-configurer les décisions nécessaires aux effets complexes, facilitant également la gestion des actions imbriquées (récursivité) comme celles de la Mairie.

Algorithme de Priorité du Pont : L'ordre du tour est géré par une clé de tri composite (-position, -priorité). Un compteur global incrémental assure que le dernier arrivant sur une case obtient toujours la priorité maximale. Cela simule mathématiquement l'empilement physique des pions sans nécessiter de structures de données complexes.

Architecture Dispatcher pour les Effets : La méthode _apply_tile_effect agit comme un routeur pour déléguer la logique. Elle détecte le type de tuile et redirige vers des méthodes spécialisées, assurant une forte modularité : modifier une règle spécifique (ex: animaux) n'a aucun impact collatéral sur les autres types de tuiles.

Machine à États du TurnManager : Le TurnManager isole la gestion du flux (actions restantes) de la validation des règles. Cette abstraction simplifie la boucle de jeu et permet d'intégrer aisément des exceptions, comme les actions gratuites, en manipulant simplement le compteur d'actions sans altérer la structure du moteur principal.

# UI implementation