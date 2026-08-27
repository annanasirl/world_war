##contiene gli scenari di partrenza (come far partire il gioco
##e come disporre i giocatori con la mappa

from . import world_map as wm
from .rules import PLAYER1, PLAYER2, NONE

STARTING_UNITS = 5


def build_easy_world():
    world = wm.init_world_easy()
    owners = [
        PLAYER1,  # 0: North America
        PLAYER1,  # 1: South America
        NONE,  # 2: Europe
        NONE,  # 3: Northern Africa
        NONE,  # 4: Southern Africa
        NONE,  # 5: West Asia
        PLAYER2,  # 6: East Asia
        PLAYER2,  # 7: Oceania
    ]
    for territory, owner in zip(world, owners):
        territory.owner = owner
        territory.units_stored = STARTING_UNITS
    return world


def build_medium_world():
    world = wm.init_world_medium()
    for territory in world:
        territory.owner = NONE
        territory.units_stored = STARTING_UNITS
    world[0].owner = PLAYER1
    world[1].owner = PLAYER1
    world[2].owner = PLAYER1
    world[23].owner = PLAYER2
    world[24].owner = PLAYER2
    world[25].owner = PLAYER2
    return world


def build_hard_world():
    world = wm.init_world_hard()
    for territory in world:
        territory.owner = NONE
        territory.units_stored = STARTING_UNITS
    world[0].owner = PLAYER1
    world[1].owner = PLAYER2
    return world

def build_italy_world():
    world = wm.init_world_italian_hunger_games()
    for territory in world:
        territory.owner = NONE
        territory.units_stored = STARTING_UNITS
        world[8].owner = PLAYER1
        world[14].owner = PLAYER2
    return world


SCENARIOS = {
    "easy": build_easy_world,
    "medium": build_medium_world,
    "hard": build_hard_world,
    "italy": build_italy_world
}


def build_world(scenario="easy"):
    if scenario not in SCENARIOS:
        raise ValueError(f"Scenario sconosciuto: '{scenario}'. Disponibili: {list(SCENARIOS)}")
    return SCENARIOS[scenario]()