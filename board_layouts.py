from board import TileType

LAYOUTS = {
    1: {
        # r = -3
        (0, -3): (TileType.ANIMAL, 6),
        (1, -3): (TileType.CASTLE, 5),
        (2, -3): (TileType.CASTLE, 4),
        (3, -3): (TileType.KNOWLEDGE, 3),

        # r = -2
        (-1, -2): (TileType.ANIMAL, 5),
        (0, -2): (TileType.ANIMAL, 4),
        (1, -2): (TileType.CASTLE, 6),
        (2, -2): (TileType.KNOWLEDGE, 2),
        (3, -2): (TileType.BUILDING, 3),

        # r = -1
        (-2, -1): (TileType.ANIMAL, 3),
        (-1, -1): (TileType.ANIMAL, 2),
        (0, -1): (TileType.BUILDING, 1),
        (1, -1): (TileType.KNOWLEDGE, 5),
        (2, -1): (TileType.BUILDING, 4),
        (3, -1): (TileType.BUILDING, 6),

        # r = 0
        (-3, 0): (TileType.SHIP, 4),
        (-2, 0): (TileType.SHIP, 3),
        (-1, 0): (TileType.SHIP, 2),
        (0, 0): (TileType.CASTLE, 6),
        (1, 0): (TileType.SHIP, 5),
        (2, 0): (TileType.SHIP, 1),
        (3, 0): (TileType.SHIP, 4),

        # r = 1
        (-3, 1): (TileType.BUILDING, 3),
        (-2, 1): (TileType.BUILDING, 2),
        (-1, 1): (TileType.MINE, 6),
        (0, 1): (TileType.BUILDING, 5),
        (1, 1): (TileType.BUILDING, 4),
        (2, 1): (TileType.ANIMAL, 1),

        # r = 2
        (-3, 2): (TileType.BUILDING, 6),
        (-2, 2): (TileType.MINE, 5),
        (-1, 2): (TileType.KNOWLEDGE, 3),
        (0, 2): (TileType.BUILDING, 2),
        (1, 2): (TileType.BUILDING, 4),

        # r = 3
        (-3, 3): (TileType.MINE, 4),
        (-2, 3): (TileType.KNOWLEDGE, 2),
        (-1, 3): (TileType.KNOWLEDGE, 1),
        (0, 3): (TileType.BUILDING, 5),
    }
}
