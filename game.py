import territory as t
import world_map as wm
import random

def calculate_odds(attacking_units, defending_units):
    ratio = attacking_units / defending_units
    odds = ratio / (ratio + 1)
    return odds

def fight(attacking_units, defending_units):
    odds = calculate_odds(attacking_units,defending_units)
    if random.random() < odds:
        return "attacker"
    else:
        return "defender"

class Game:
    def __init__(self, mappa):
        self.mappa = mappa
        self.players = []

    def attack(self, attacker, defender, troops):
        # Controlli preliminari
        if attacker == defender:
            print("attacker and defender are same")
            return False
        if attacker.get_owner() == defender.get_owner():
            print("attacker and defender have same owner")
            return False
        if defender not in attacker.get_neighbors():
            print("defender is not in attacker's neighbors")
            return False
        if troops <= 0:
            print("troops must be positive")
            return False
        if troops >= attacker.get_units_stored():
            print("you must leave at least one unit in the territory")
            return False
        if defender.get_owner() == "none":
            defender.owner = attacker.get_owner()
            defender.units_stored = troops
            attacker.units_stored -= troops
            print("territory conquered without fight")
            return True

        attacking_units = troops
        while attacking_units > 0 and defender.get_units_stored() > 0:
            winner = fight(attacking_units,defender.get_units_stored())
            if winner == "attacker":
                defender.units_stored -= 1
                print("defender loses 1 unit")
            else:
                attacking_units -= 1
                print("attacker loses 1 unit")

        attacker.units_stored -= troops

        if defender.units_stored <= 0:
            defender.owner = attacker.owner
            defender.units_stored = attacking_units
            print("territory conquered!")
        return True

    def move_troops(self, source, destination, troops):
        if source == destination:
            print("source and destination are the same")
            return False
        if source.get_owner() != destination.get_owner():
            print("you can only move troops between your territories")
            return False
        if destination not in source.get_neighbors():
            print("destination is not a neighbor of source")
            return False
        if troops <= 0:
            print("troops must be positive")
            return False
        if troops >= source.get_units_stored():
            print("you must leave at least one unit in the source territory")
            return False
        source.units_stored -= troops
        destination.units_stored += troops
        print(
            f"{troops} troops moved from "
            f"{source.get_name()} to {destination.get_name()}"
        )
        return True

    def step(self, action):
        action_type = action[0]
        if action_type == "attack":
            attacker = action[1]
            defender = action[2]
            troops = action[3]
            success = self.attack(attacker,defender,troops)
            if not success:
                return self.get_state(), -10, False
            reward = self.calculate_reward()
            done = self.check_game_over()
            return self.get_state(), reward, done
        else:
            print("unknown action")
            return self.get_state(), -10, False

    def get_state(self):
        state = []
        for territory in self.mappa:
            state.append(territory.get_owner())
            state.append(territory.get_units_stored())
        return state

    def calculate_reward(self):
        player_territories = 0
        enemy_territories = 0
        for territory in self.mappa:
            if territory.get_owner() == 0:
                player_territories += 1
            elif territory.get_owner() == 1:
                enemy_territories += 1
        return player_territories - enemy_territories

    def check_game_over(self):
        owners = set()
        for territory in self.mappa:
            owners.add(territory.get_owner())
        return len(owners) == 1

    def end_turn(self):
        for territory in self.mappa:
            if territory.get_owner() != "none":
                territory.produce_units()

    def play_attack(self):
        print("\nChoose your territory to attack from.")
        choice = int(input("> "))
        if choice < 0 or choice >= len(self.mappa):
            print("Invalid territory.")
            return
        attacker = self.mappa[choice]
        # Controlliamo che il territorio sia del giocatore
        if attacker.get_owner() != "player":
            print("This is not your territory.")
            return
        # Mostriamo i vicini
        print(f"\nNeighbors of {attacker.get_name()}:")

        for i, neighbor in enumerate(attacker.get_neighbors()):
            print(
                f"{i}: {neighbor.get_name()} | "
                f"Owner: {neighbor.get_owner()} | "
                f"Units: {neighbor.get_units_stored()}"
            )

        choice = int(input("Choose a territory to attack: "))
        neighbors = attacker.get_neighbors()
        if choice < 0 or choice >= len(neighbors):
            print("Invalid territory.")
            return
        defender = neighbors[choice]
        # Quante truppe mandare?
        print(
            f"\nYou have {attacker.get_units_stored()} "
            f"units in {attacker.get_name()}."
        )
        troops = int(input("How many troops do you want to attack with? "))

        result = self.attack(attacker, defender, troops)
        if result:
            print("\nAttack completed.")

    def play_move(self):
        print("\nChoose source territory:")
        for i, territory in enumerate(self.mappa):
            if territory.get_owner() == "player":
                print(
                    f"{i}: {territory.get_name()} "
                    f"[{territory.get_units_stored()} units]"
                )

        source_id = int(input("> "))
        source = self.mappa[source_id]
        print(f"\nNeighbors of {source.get_name()}:")
        for i, neighbor in enumerate(source.get_neighbors()):
            if neighbor.get_owner() == "player":
                print(
                    f"{i}: {neighbor.get_name()} "
                    f"[{neighbor.get_units_stored()} units]"
                )
        destination_id = int(input("> "))
        neighbors = source.get_neighbors()
        if destination_id < 0 or destination_id >= len(neighbors):
            print("Invalid territory.")
            return
        destination = neighbors[destination_id]
        troops = int(input("How many troops do you want to move? "))
        self.move_troops(source,destination,troops)

    def play(self):
        while True:
            print("\n==============================")
            print("          WORLD CONQUEST")
            print("==============================")
            # Mostra tutti i territori
            for i, territory in enumerate(self.mappa):
                print(
                    f"{i}: {territory.get_name()} | "
                    f"Owner: {territory.get_owner()} | "
                    f"Units: {territory.get_units_stored()}"
                )

            print("\nWhat do you want to do?")
            print("1. Attack")
            print("2. Move troops")
            print("3. End turn")

            choice = int(input("> "))

            if choice == 1:
                self.play_attack()

            elif choice == 2:
                self.play_move()

            elif choice == 3:
                self.end_turn()

            else:
                print("Invalid choice.")

            if self.check_game_over():
                print("\n==============================")
                print("       YOU WON! 🎉")
                print("==============================")
                break

            self.end_turn()
            input("\nEnd turn. units produced. press enter to continue...")