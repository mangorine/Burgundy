
from random import randint
class Player:
    """
    Classe représentant un joueur dans The Castles of Burgundy.
    """

    def __init__(self, color, turn_order, board):
        # Identité du joueur
        self.color = color            # couleur du joueur
        self.turn_order = turn_order  # position dans l'ordre du tour

        # Ressources
        self.vp = 0          # points de victoire
        self.workers = 0     # ouvriers / paysans
        self.silver = 0      # pièces d'argent

        # Dés (2 dés utilisés pour réaliser les actions)
        self.dice = [1,1]
        self.used_dice = [False, False]  # pour suivre quels dés ont été utilisés dans le tour

        # Tuiles (stock temporaire avant placement sur le domaine)
        self.available_tiles = []  

        # Domaine personnel: coordonnées -> tuile ou None
        self.board = board 
        # Marchandises : type -> nombre
        self.goods = {} 

        # Effets jaunes actifs sur le joueur
        self.yellow_effects = []  


    
    # MÉTHODES ESSENTIELLES 


    def roll_dice(self):
        """Définit les valeurs des deux dés (temporaire en attendant RNG)."""
        self.dice = [randint(1,6),randint(1,6)]
        self.used_dice = [False, False]

    def adjust_dice(self, dice_idx, delta):
        """Utilise des ouvriers pour modifier un dé de +1/-1 par ouvrier."""
        cost = abs(delta)
        if self.workers < cost:
            raise ValueError("Pas assez d'ouvriers pour ajuster le dé !")
        self.workers -= cost
        new_val = self.dice[dice_idx] + delta
        self.dice[dice_idx] = new_val

    def gain_goods(self, good_type, amount=1):
        if good_type in self.goods.keys():
            self.goods[good_type] = self.goods[good_type] + amount 
        else:
            self.goods[good_type]=1

    def sell_goods(self, good_type):
        qty = self.goods[good_type]
        if qty <= 0:
            raise ValueError("Aucune marchandise à vendre !")
        self.silver += 1
        self.goods[good_type] =0

    def gain_silver(self, amount):
        self.silver += amount

    def spend_silver(self, amount):
        if self.silver < amount:
            raise ValueError("Pas assez de pièces !")
        self.silver -= amount

    def can_place(self, position, tile):
        """
        Vérifie simplement que la case existe et est vide.
        TODO: calcul voisins(hexagon) et voir possibilité
        """
        #reste à vérifier si voisin à la pos actuelle et 
        #si les chiffres sur la tile et la pos sont compatibles
        return position in self.board and self.board[position] is None

    def place_tile(self, position, tile):
        if not self.can_place(position, tile):
            raise ValueError("Placement de tuile impossible !")
        self.board[position] = tile
        self.apply_tile_effect(tile)

    def apply_tile_effect(self, tile):
        """Déclenche les effets immédiats des tuiles.
        """
        t = tile.type
        if t == "SHIP":
            self.advance_turn_order()  # priorité au tour !
        elif t == "MINE":
            pass  # revenu en fin de manche 
        elif t=="ANIMAL":
            pass #gestion animaux en fin de partie
        elif t=="CASTLE":
             pass 
         #je sais pas comment gérer l'action du château pour l'instant #
         # (une liste de possible actions et exécuter une)
        elif t == "KNOWLEDGE":
            tag = tile.ability_tag
            if tag:
                self.yellow_effects.append(tag)



    def __str__(self):
        return f"Player {self.color} | VP: {self.vp} | Silver: {self.silver} | Workers: {self.workers} | Dice: {self.dice}"


    #  IMPORTANTS RESTANTS
    # GESTION Des bateaux
    # - Vérification complète de placement selon la géométrie et les types
    # - Interactions avec le marché central
    # - Revenus de mines + bonus de zones
    # - Gestion avancée des tuiles jaunes selon règles officielles
    # - Gestion de fin de partie et scoring total
    # - Lancement automatique des dés + relances selon paysans
