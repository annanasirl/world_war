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


def attack(attacker, defender, troops):
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


def move_troops(source, destination, troops):
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


class Game:
    def __init__(self, mappa):
        self.mappa = mappa
        self.players = []

    def step(self, action):
        action_type = action[0]
        if action_type == "attack":
            attacker = action[1]
            defender = action[2]
            troops = action[3]
            success = attack(attacker,defender,troops)
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
        player_won = True
        enemy_won = True
        for territory in self.mappa:
            if territory.get_owner() == "enemy":
                player_won = False
            if territory.get_owner() == "player":
                enemy_won = False
        if player_won:
            return "player"
        if enemy_won:
            return "enemy"
        return None

    def end_turn(self):
        return
        # for territory in self.mappa:
        #     if territory.get_owner() != "none":
        #         territory.produce_units()

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

        result = attack(attacker, defender, troops)
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
        move_troops(source,destination,troops)

    def calculate_reinforcements(self, owner):
        units = 0
        for territory in self.mappa:
            if territory.get_owner() == owner:
                units += territory.get_units_produced()
        return units

    def deploy_units(self, owner):
        units = self.calculate_reinforcements(owner)
        territory_list = [t for t in self.mappa if t.get_owner() == owner]

        print(f"\nYou have {units} units to deploy.")
        for t in territory_list:
            if units <= 0:
                return
            print(
                f"\n{t.get_name()} | "
                f"Units: {t.get_units_stored()} | "
                f"Units available: {units}"
            )
            print(f"How many units do you want to deploy to {t.get_name()}?")
            deployed = int(input("> "))
            if deployed > 0 and deployed <= units:
                t.add_units(deployed)
                units -= deployed
            else:
                print(f"Invalid number. Zero units deployed to {t.get_name()}.")

    def bot_deploy_units(self):
        units = self.calculate_reinforcements("enemy")
        territory_list = [t for t in self.mappa if t.get_owner() == "enemy"]

        while units > 0 and territory_list:
            t = random.choice(territory_list)
            deployed = random.randint(1, units)
            t.add_units(deployed)
            units -= deployed
            print(f"Enemy deploys {deployed} units to {t.get_name()}.")

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

            self.deploy_units("player")

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

            winner = self.check_game_over()
            if winner == "player":
                print("YOU WON!")
                break
            elif winner == "enemy":
                print("YOU LOST!")
                break
            else:
                print("Game continues.")

            self.end_turn()
            input("\nPress ENTER for enemy turn...")

            winner = self.bot_play()
            if winner == "player":
                print("\nYOU WON!")
                break
            elif winner == "enemy":
                print("\nYOU LOST!")
                break
            input("\nPress ENTER for your turn...")

    def bot_play(self):

        print("\n==============================")
        print("        ENEMY TURN")
        print("==============================")

        self.bot_deploy_units()

        possible_actions = []
        # ATTACK POSSIBILI
        for territory in self.mappa:
            if territory.get_owner() != "enemy":
                continue
            if territory.get_units_stored() <= 1:
                continue
            for neighbor in territory.get_neighbors():
                if neighbor.get_owner() == "player":
                    max_troops = territory.get_units_stored() - 1
                    for troops in range(1, max_troops + 1):
                        possible_actions.append(("attack", territory, neighbor, troops))
        # MOVE POSSIBILI
        for territory in self.mappa:
            if territory.get_owner() != "enemy":
                continue
            if territory.get_units_stored() <= 1:
                continue
            for neighbor in territory.get_neighbors():
                if neighbor.get_owner() == "enemy":
                    max_troops = territory.get_units_stored() - 1
                    for troops in range(1, max_troops + 1):
                        possible_actions.append(("move", territory, neighbor, troops))

        possible_actions.append(("nothing",))
        action = random.choice(possible_actions)
        if action[0] == "nothing":
            print("Enemy does nothing.")
        elif action[0] == "attack":
            _, attacker, defender, troops = action
            print(
                f"Enemy attacks {defender.get_name()} "
                f"from {attacker.get_name()} "
                f"with {troops} troops."
            )
            attack(attacker, defender, troops)
        elif action[0] == "move":
            _, source, destination, troops = action
            print(
                f"Enemy moves {troops} troops "
                f"from {source.get_name()} "
                f"to {destination.get_name()}."
            )
            move_troops(source, destination, troops)
        # Fine turno bot
        self.end_turn()
        return self.check_game_over()