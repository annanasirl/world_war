import random

# ---------------------------------------------------------------------------
# Costanti owner
# ---------------------------------------------------------------------------
PLAYER = "player"
ENEMY  = "enemy"
NONE   = "none"

# ---------------------------------------------------------------------------
# Costanti fase di gioco — usate da Game.phase e da step()
# ---------------------------------------------------------------------------
PHASE_DEPLOY  = "deploy"   # spartizione truppe nuove
PHASE_ACTION  = "action"   # attacco OPPURE spostamento

# ---------------------------------------------------------------------------
# Funzioni di combattimento
# ---------------------------------------------------------------------------

def calculate_odds(attacking_units, defending_units):
    ratio = attacking_units / defending_units
    odds = ratio / (ratio + 1)
    return odds

def fight(attacking_units, defending_units):
    odds = calculate_odds(attacking_units, defending_units)
    return "attacker" if random.random() < odds else "defender"

def attack(attacker, defender, troops):
    """
    Risolve un attacco. Restituisce True se l'azione è valida, False altrimenti.
    Bug fix: le truppe dell'attaccante venivano scalate due volte.
    """
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
    """Sposta truppe tra due territori dello stesso proprietario."""
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


# ---------------------------------------------------------------------------
# Classe Game
# ---------------------------------------------------------------------------

class Game:
    """
    Ambiente di gioco compatibile con il loop RL.

    Struttura di ogni turno (per ciascun giocatore):
      1. PHASE_DEPLOY  — distribuisci le truppe nuove sui tuoi territori
      2. PHASE_ACTION  — attacca UN territorio nemico OPPURE sposta truppe

    step(action) gestisce entrambe le fasi e avanza automaticamente
    alla fase successiva (e al turno del bot quando necessario).

    Formato delle azioni:
      Fase deploy  -> ("deploy", territorio, quantità)
      Fase action  -> ("attack", attaccante, difensore, truppe)
                   -> ("move",   sorgente,   destinazione, truppe)
                   -> ("pass",)   # salta la fase azione
    """

    def __init__(self, mappa, verbose = False):
        self.mappa   = mappa
        self.phase   = PHASE_DEPLOY
        self.current_player = PLAYER
        # Salva lo stato iniziale per reset()
        self._initial_state = [(t.owner, t.units_stored) for t in self.mappa]
        # truppe ancora da piazzare nella fase deploy
        self._deploy_pool = self.calculate_reinforcements(PLAYER)
        self.verbose = verbose
        self._deploy_territories = [t for t in self.mappa if t.get_owner() == PLAYER]
        self._deploy_index = 0

    # ------------------------------------------------------------------
    # funzioni per RL
    # ------------------------------------------------------------------

    def reset(self):
        for t, (owner, units) in zip(self.mappa, self._initial_state):
            t.owner       = owner
            t.units_stored = units
        self.phase               = PHASE_DEPLOY
        self._deploy_pool        = self.calculate_reinforcements(PLAYER)
        self._deploy_territories = [t for t in self.mappa if t.get_owner() == PLAYER]
        self._deploy_index       = 0
        return self.get_state()

    def get_legal_actions(self):
        if self.phase == PHASE_DEPLOY:
            # Solo il territorio corrente nella sequenza di deploy
            if self._deploy_index >= len(self._deploy_territories):
                return [("deploy", None, 0)]  # segnale di fine deploy
            t = self._deploy_territories[self._deploy_index]
            return [("deploy", t, amount) for amount in range(0, self._deploy_pool + 1)]

        if self.phase == PHASE_ACTION:
            actions = [("pass",)]
            for t in self.mappa:
                if t.get_owner() != PLAYER or t.get_units_stored() <= 1:
                    continue
                max_t = t.get_units_stored() - 1
                for neighbor in t.get_neighbors():
                    if neighbor.get_owner() != PLAYER:
                        for troops in range(1, max_t + 1):
                            actions.append(("attack", t, neighbor, troops))
                    else:
                        for troops in range(1, max_t + 1):
                            actions.append(("move", t, neighbor, troops))
            return actions

        return []

    # ------------------------------------------------------------------
    # Interfaccia RL principale
    # ------------------------------------------------------------------

    def step(self, action):
        """
        Esegui un'azione. Restituisce (state, reward, done).
        reward = 0 per azioni valide intermedie
        reward = -10 per azioni non valide
        reward = +100 / -100 per fine partita
        """
        action_type = action[0]

        # --- Fase deploy ---
        if self.phase == PHASE_DEPLOY:
            if action_type != "deploy":
                return self.get_state(), -10, False

            _, territory, amount = action

            if amount < 0 or amount > self._deploy_pool:
                return self.get_state(), -10, False

            if territory is not None:
                if territory.get_owner() != PLAYER:
                    return self.get_state(), -10, False
                territory.add_units(amount)
                self._deploy_pool -= amount

            # Avanza al territorio successivo
            self._deploy_index += 1

            # Avanza a PHASE_ACTION se abbiamo visitato tutti i territori
            # oppure se il pool è esaurito
            if self._deploy_index >= len(self._deploy_territories) or self._deploy_pool == 0:
                self.phase = PHASE_ACTION
                self._deploy_index = 0

            return self.get_state(), 0, False

        # --- Fase action ---
        if self.phase == PHASE_ACTION:
            if action_type == "attack":
                _, attacker, defender, troops = action
                if attacker.get_owner() != self.current_player:
                    return self.get_state(), -10, False
                success = attack(attacker, defender, troops)
                if not success:
                    if self.verbose:
                        print("[PLAYER] Invalid attack.")
                    return self.get_state(), -10, False
                if self.verbose:
                    if defender.get_owner() == PLAYER:
                        print(f"[PLAYER] Attacked {defender.get_name()} with {troops} troops -> Territory conquered!")
                    else:
                        print(
                            f"[PLAYER] Attacked {defender.get_name()} with {troops} troops -> Attack failed. Enemy holds with {defender.get_units_stored()} units.")

            elif action_type == "move":
                _, source, destination, troops = action
                if source.get_owner() != self.current_player:
                    return self.get_state(), -10, False
                success = move_troops(source, destination, troops)
                if not success:
                    if self.verbose:
                        print("[PLAYER] Invalid move.")
                    return self.get_state(), -10, False
                if self.verbose:
                    print(f"[PLAYER] Moved {troops} troops from {source.get_name()} to {destination.get_name()}.")

            elif action_type == "pass":
                if self.verbose:
                    print("[PLAYER] No action taken.")
                pass  # il giocatore salta la fase azione

            else:
                return self.get_state(), -10, False

            # Controlla fine partita dopo ogni azione
            winner = self.check_game_over()
            if winner == PLAYER:
                return self.get_state(), 100, True
            if winner == ENEMY:
                return self.get_state(), -100, True

            # Passa al turno del bot
            self._run_bot_turn()

            winner = self.check_game_over()
            if winner == PLAYER:
                return self.get_state(), 100, True
            if winner == ENEMY:
                return self.get_state(), -100, True

            # Prepara il turno successivo del giocatore
            self.phase = PHASE_DEPLOY
            self._deploy_pool = self.calculate_reinforcements(PLAYER)
            self._deploy_territories = [t for t in self.mappa if t.get_owner() == PLAYER]
            self._deploy_index = 0

            return self.get_state(), self.calculate_reward(), False

        return self.get_state(), -10, False

    # ------------------------------------------------------------------
    # Stato e reward
    # ------------------------------------------------------------------

    def get_state(self):
        """
        Restituisce lo stato corrente come lista piatta:
        [owner_t0, units_t0, owner_t1, units_t1, ...]
        Gli owner sono stringhe; tocca all'algoritmo RL encodarle.
        """
        state = []
        for territory in self.mappa:
            state.append(territory.get_owner())
            state.append(territory.get_units_stored())
        return state

    def calculate_reward(self):
        """Reward intermedia: differenza tra territori player e territori enemy."""
        player_t = sum(1 for t in self.mappa if t.get_owner() == PLAYER)
        enemy_t  = sum(1 for t in self.mappa if t.get_owner() == ENEMY)
        return player_t - enemy_t

    def check_game_over(self):
        """Restituisce 'player', 'enemy' o None."""
        owners = {t.get_owner() for t in self.mappa}
        if ENEMY not in owners:
            return PLAYER
        if PLAYER not in owners:
            return ENEMY
        return None

    # ------------------------------------------------------------------
    # Rinforzi
    # ------------------------------------------------------------------

    def calculate_reinforcements(self, owner):
        return sum(t.get_units_produced() for t in self.mappa if t.get_owner() == owner)

    def _try_advance_from_deploy(self):
        """Avanza alla fase azione se il pool è esaurito."""
        if self._deploy_pool == 0:
            self.phase = PHASE_ACTION

    # ------------------------------------------------------------------
    # Turno del bot (random)
    # ------------------------------------------------------------------

    def _run_bot_turn(self):
        if self.verbose:
            print("          ENEMY TURN")
        self._bot_deploy()
        self._bot_action()
        if self.verbose:
            print("\n[ENEMY] Turn ended.")

    def _bot_deploy(self):
        units = self.calculate_reinforcements(ENEMY)
        territory_list = [t for t in self.mappa if t.get_owner() == ENEMY]
        if self.verbose:
            print(f"\n[ENEMY] Deploying {units} reinforcement units...")
        while units > 0 and territory_list:
            t = random.choice(territory_list)
            deployed = random.randint(1, units)
            t.add_units(deployed)
            units -= deployed
            if self.verbose:
                print(f"  -> {deployed} units deployed to {t.get_name()} (now {t.get_units_stored()} total)")

    def _bot_action(self):

        actions = []

        for t in self.mappa:
            if t.get_owner() != ENEMY or t.get_units_stored() <= 1:
                continue
            max_t = t.get_units_stored() - 1
            for neighbor in t.get_neighbors():
                if neighbor.get_owner() != ENEMY:
                    for troops in range(1, max_t + 1):
                        actions.append(("attack", t, neighbor, troops))
                else:
                    for troops in range(1, max_t + 1):
                        actions.append(("move", t, neighbor, troops))

        actions.append(("pass",))
        chosen = random.choice(actions)

        if chosen[0] == "attack":
            _, attacker, defender, troops = chosen
            prev_owner = defender.get_owner()
            attack(attacker, defender, troops)
            if self.verbose:
                if defender.get_owner() == ENEMY:
                    print(f"\n[ENEMY] Attacked {defender.get_name()} from {attacker.get_name()} with {troops} troops -> Territory conquered!")
                else:
                    print(f"\n[ENEMY] Attacked {defender.get_name()} from {attacker.get_name()} with {troops} troops -> Attack failed. {defender.get_name()} holds with {defender.get_units_stored()} units.")
        elif chosen[0] == "move":
            _, source, destination, troops = chosen
            move_troops(source, destination, troops)
            if self.verbose:
                print(f"\n[ENEMY] Moved {troops} troops from {source.get_name()} to {destination.get_name()}.")
        else:
            if self.verbose:
                print("\n[ENEMY] No action taken.")

    # ------------------------------------------------------------------
    # Modalità giocatore umano (per test manuali)
    # ------------------------------------------------------------------

    def play(self):
        while True:
            print("\n==============================")
            print("          WORLD CONQUEST")
            print("==============================")
            for i, t in enumerate(self.mappa):
                print(f"{i}: {t.get_name()} | Owner: {t.get_owner()} | Units: {t.get_units_stored()}")

            # Fase deploy
            self._human_deploy()

            # Fase azione
            print("\nWhat do you want to do?")
            print("1. Attack")
            print("2. Move troops")
            print("3. Pass")
            choice = int(input("> "))

            if choice == 1:
                action = self._human_build_attack()
            elif choice == 2:
                action = self._human_build_move()
            else:
                action = ("pass",)

            state, reward, done = self.step(action)

            winner = self.check_game_over()
            if winner == PLAYER:
                print("YOU WON!")
                break
            elif winner == ENEMY:
                print("YOU LOST!")
                break

            input("\nPress ENTER to continue...")

    def _human_deploy(self):
        units = self.calculate_reinforcements(PLAYER)
        territory_list = [t for t in self.mappa if t.get_owner() == PLAYER]
        print(f"\nYou have {units} units to deploy.")
        for t in territory_list:
            if units <= 0:
                break
            print(f"\n{t.get_name()} | Units: {t.get_units_stored()} | Available: {units}")
            deployed = int(input("How many units to deploy here? "))
            if 0 < deployed <= units:
                self.step(("deploy", t, deployed))
                units -= deployed
            else:
                print("Invalid. Zero units deployed here.")
        # esaurisce la fase deploy
        self.phase = PHASE_ACTION

    def _human_build_attack(self):
        print("\nChoose your territory to attack from (index):")
        for i, t in enumerate(self.mappa):
            if t.get_owner() == PLAYER:
                print(f"  {i}: {t.get_name()} [{t.get_units_stored()} units]")
        attacker = self.mappa[int(input("> "))]

        print("Choose a neighbor to attack (index):")
        neighbors = attacker.get_neighbors()
        for i, n in enumerate(neighbors):
            print(f"  {i}: {n.get_name()} | Owner: {n.get_owner()} | Units: {n.get_units_stored()}")
        defender = neighbors[int(input("> "))]

        troops = int(input(f"How many troops? (max {attacker.get_units_stored() - 1}) "))
        return ("attack", attacker, defender, troops)

    def _human_build_move(self):
        print("\nChoose source territory (index):")
        for i, t in enumerate(self.mappa):
            if t.get_owner() == PLAYER:
                print(f"  {i}: {t.get_name()} [{t.get_units_stored()} units]")
        source = self.mappa[int(input("> "))]

        print("Choose destination (index):")
        neighbors = source.get_neighbors()
        for i, n in enumerate(neighbors):
            if n.get_owner() == PLAYER:
                print(f"  {i}: {n.get_name()} [{n.get_units_stored()} units]")
        destination = neighbors[int(input("> "))]

        troops = int(input(f"How many troops? (max {source.get_units_stored() - 1}) "))
        return ("move", source, destination, troops)