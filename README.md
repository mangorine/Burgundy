# Burgundy

BOARD GAME : CASTLES OF BURGUNDY

# Rules of the game

Rules of the games here : [Rules](rules_burgundy.pdf)

# Class Building

## Variable names used in reference of Player class

In the building class, we assumed that the following attributes and methods existed.
Attributes:
- silverlings (number of silverlings)
- goods (list of the goods)
- full (boolean that tells us if the player's inventory is full or not)
- personal_slots (list of the tiles of the inventory)
- workers (number of workers)

Methods:
- choose(str:name) (it takes a parameter name which corresponds to the tile effect and lets the player choose tiles according to the effect in place, it return the tile chosen)
- sell_good(good) (sells the good in question, don't forget to delete the good from the good inventory and to add the number of coins the player receives from the sell action)

## Variable names used in reference of Board class

In the Board class, we assumed that the following attributes and methods existed.
Attributes:
- building (list of buildings on the board)
- castle (list of castles on the board)
- mine (list of mines on the board)
- knowledge (list of knowledge tiles on the board)

Methods:
- 
# Class board 

To do : inter exclusive buildings : page 6.

# Class Action

We create a class Action with the following actions:
- Trade a die with a worker or a gold
- Sell a good
- Take a tile (from the board)
- Buy a center tile (only once per phase)
- Place a tile
- Change die value
- Discard a tile

# How the game works

Before each phase : [Phase](game_tuto.png)


# things to do Emilie:
check the action of every yellow tiles and add modifications where the action is taken into account

# things to do:
BIG THING: finish board, player board
            then create a real player.py which will be connected to the two last files
             change the methods with the yellow tiles

little things, example of things to do in the last part:
make a method that checks whether you can put a tile in your board (vicinity + building in the same town)
after that: Emilie adds a method to implement yellow tile n°1
