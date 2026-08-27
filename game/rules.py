##contiene le regole del gioco

import random

PLAYER1 = "player1"
PLAYER2 = "player2"
NONE = "none"

PHASE_DEPLOY = "deploy"  # spartizione truppe nuove
PHASE_ACTION = "action"  # attacco o spostamento o passo

def calculate_odds(attacking_units, defending_units):
    ratio = attacking_units / defending_units
    odds = ratio / (ratio + 1)
    return odds

def fight(attacking_units, defending_units):
    odds = calculate_odds(attacking_units, defending_units)
    return "attacker" if random.random() < odds else "defender"

def attack(attacker, defender, troops):
    if attacker == defender:
        return False
    if attacker.get_owner() == defender.get_owner():
        return False
    if defender not in attacker.get_neighbors():
        return False
    if troops <= 0:
        return False
    if troops >= attacker.get_units_stored():
        return False

    # Conquista senza combattimento
    if defender.get_owner() == NONE:
        attacker.units_stored -= troops
        defender.owner = attacker.get_owner()
        defender.units_stored = troops
        return True

    # Combattimento
    attacking_units = troops
    defending_units = defender.get_units_stored()

    while attacking_units > 0 and defending_units > 0:
        if fight(attacking_units, defending_units) == "attacker":
            defending_units -= 1
        else:
            attacking_units -= 1

    # Scala le truppe dell'attaccante una volta sola, a fine combattimento
    attacker.units_stored -= troops

    if defending_units <= 0:
        defender.owner = attacker.get_owner()
        defender.units_stored = attacking_units
    else:
        defender.units_stored = defending_units

    return True


def move_troops(source, destination, troops):
    if source == destination:
        return False
    if source.get_owner() != destination.get_owner():
        return False
    if destination not in source.get_neighbors():
        return False
    if troops <= 0:
        return False
    if troops >= source.get_units_stored():
        return False
    source.units_stored -= troops
    destination.units_stored += troops
    return True

def troop_options(max_t):
    options = {
        max(1, int(max_t * 0.25)),
        max(1, int(max_t * 0.50)),
        max(1, int(max_t * 0.75)),
        max_t
    }
    return sorted(options)