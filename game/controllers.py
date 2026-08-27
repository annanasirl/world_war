#qui sta il codice che gestisce la decisione delle mosse
#di enemy e di player

import random
from .rules import PLAYER2, PLAYER1, attack, move_troops, troop_options, PHASE_DEPLOY


class RandomController:
    def choose_action(self, game, player):
        legal_actions = game.get_legal_actions(player)
        return random.choice(legal_actions)

class HumanController:
    def choose_action(self, game, player):
        if game.phase == PHASE_DEPLOY:
            return self._build_deploy(game, player)
        print("\nWhat do you want to do?")
        print("1. Attack")
        print("2. Move troops")
        print("3. Pass")
        choice = self._ask_int("> ")
        if choice == 1:
            return self._build_attack(game, player)
        if choice == 2:
            return self._build_move(game, player)
        return ("pass",)

    def _build_deploy(self, game, player):
        legal_actions = game.get_legal_actions(player)
        territory = legal_actions[0][1]  # tutte le azioni si riferiscono allo stesso territorio
        if territory is None:
            return ("deploy", None, 0)
        pool = game.get_deploy_pool()
        print(f"\n{territory.get_name()} | Units: {territory.get_units_stored()} | Available: {pool}")
        amount = self._ask_int(f"How many units to deploy here? (0-{pool}) ")
        if 0 <= amount <= pool:
            return ("deploy", territory, amount)
        print("Invalid. Zero units deployed here.")
        return ("deploy", territory, 0)

    def _build_attack(self, game, player):
        print("\nChoose your territory to attack from (index):")
        for i, t in enumerate(game.mappa):
            if t.get_owner() == player:
                print(f"  {i}: {t.get_name()} [{t.get_units_stored()} units]")
        attacker = self._ask_territory(game.mappa)
        print("Choose a neighbor to attack (index):")
        neighbors = attacker.get_neighbors()
        for i, n in enumerate(neighbors):
            print(f"  {i}: {n.get_name()} | Owner: {n.get_owner()} | Units: {n.get_units_stored()}")
        defender = self._ask_territory(neighbors)
        troops = self._ask_int(f"How many troops? (max {attacker.get_units_stored() - 1}) ")
        return ("attack", attacker, defender, troops)

    def _build_move(self, game, player):
        print("\nChoose source territory (index):")
        for i, t in enumerate(game.mappa):
            if t.get_owner() == player:
                print(f"  {i}: {t.get_name()} [{t.get_units_stored()} units]")
        source = self._ask_territory(game.mappa)
        print("Choose destination (index):")
        neighbors = source.get_neighbors()
        for i, n in enumerate(neighbors):
            if n.get_owner() == player:
                print(f"  {i}: {n.get_name()} [{n.get_units_stored()} units]")
        destination = self._ask_territory(neighbors)
        troops = self._ask_int(f"How many troops? (max {source.get_units_stored() - 1}) ")
        return ("move", source, destination, troops)

    @staticmethod
    def _ask_int(prompt):
        try:
            return int(input(prompt))
        except ValueError:
            return -1

    @staticmethod
    def _ask_territory(options):
        while True:
            idx = HumanController._ask_int("> ")
            if 0 <= idx < len(options):
                return options[idx]
            print(f"Indice non valido, scegli un numero tra 0 e {len(options) - 1}.")


class DQNController:
    def __init__(self, agent):
        self.agent = agent

    def choose_action(self, game, player):
        legal_actions = game.get_legal_actions(player)
        deploy_pool = game.get_deploy_pool() if game.phase == PHASE_DEPLOY else None
        state = game.get_state() if player == PLAYER1 else game.get_swapped_state()
        return self.agent.choose_action(state, legal_actions, deploy_pool=deploy_pool)
