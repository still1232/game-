# Game Settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TILE_SIZE = 4  # Mỗi pixel game = 4x4 screen pixels

# World settings
WORLD_WIDTH = 512  # Số pixel ngang
WORLD_HEIGHT = 256  # Số pixel dọc
CHUNK_SIZE = 64  # Kích thước chunk

# Physics
GRAVITY = 0.5
LIQUID_FLOW_SPEED = 1
FIRE_SPREAD_CHANCE = 0.3

# Player
PLAYER_SPEED = 5
PLAYER_JUMP = -10
PLAYER_JETPACK_FORCE = -8
PLAYER_MAX_HP = 100

# Materials (IDs)
AIR = 0
SAND = 1
WATER = 2
LAVA = 3
STONE = 4
WOOD = 5
FIRE = 6
SMOKE = 7
ASH = 8
ACID = 9
ICE = 10

# Material properties
MATERIAL_PROPS = {
    AIR: {'name': 'air', 'solid': False, 'liquid': False, 'gas': False, 'flammable': False, 'color': (0, 0, 0, 0)},
    SAND: {'name': 'sand', 'solid': True, 'liquid': False, 'gas': False, 'flammable': False, 'color': (235, 200, 115, 255)},
    WATER: {'name': 'water', 'solid': False, 'liquid': True, 'gas': False, 'flammable': False, 'color': (64, 164, 223, 200)},
    LAVA: {'name': 'lava', 'solid': False, 'liquid': True, 'gas': False, 'flammable': True, 'color': (207, 16, 32, 255), 'heat': 100},
    STONE: {'name': 'stone', 'solid': True, 'liquid': False, 'gas': False, 'flammable': False, 'color': (128, 128, 128, 255)},
    WOOD: {'name': 'wood', 'solid': True, 'liquid': False, 'gas': False, 'flammable': True, 'color': (139, 90, 43, 255)},
    FIRE: {'name': 'fire', 'solid': False, 'liquid': False, 'gas': True, 'flammable': False, 'color': (255, 100, 0, 255), 'heat': 50, 'lifetime': 30},
    SMOKE: {'name': 'smoke', 'solid': False, 'liquid': False, 'gas': True, 'flammable': False, 'color': (100, 100, 100, 150), 'lifetime': 60},
    ASH: {'name': 'ash', 'solid': True, 'liquid': False, 'gas': False, 'flammable': False, 'color': (80, 80, 80, 255)},
    ACID: {'name': 'acid', 'solid': False, 'liquid': True, 'gas': False, 'flammable': False, 'color': (100, 255, 50, 200)},
    ICE: {'name': 'ice', 'solid': True, 'liquid': False, 'gas': False, 'flammable': False, 'color': (200, 230, 255, 255)},
}

# Reactions
REACTIONS = {
    (WATER, LAVA): STONE,
    (FIRE, WOOD): ASH,
    (ACID, STONE): SAND,
    (ACID, WOOD): ASH,
    (LAVA, WATER): STONE,
}
