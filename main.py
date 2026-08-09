import world_map as wm
from game import Game


# Creo la mappa
world = wm.init_world()

# Assegno i territori al giocatore
world[0].owner = "player"   # North America
world[1].owner = "player"   # South America
world[2].owner = "none"    # Europe
world[3].owner = "none"    # Northern Africa
world[4].owner = "none"    # Southern Africa
world[5].owner = "none"    # West Asia
world[6].owner = "enemy"    # East Asia
world[7].owner = "enemy"    # Oceania


for territory in world:
    territory.units_stored = 5


# Creo la partita
game = Game(world)

# Inizio a giocare
game.play()