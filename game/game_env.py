from .rules import PLAYER1, PLAYER2, PHASE_DEPLOY, PHASE_ACTION, attack, move_troops, troop_options

from .controllers import RandomController

class Game:
    def __init__(self, mappa, verbose=False):
        self.mappa = mappa
        self.phase = PHASE_DEPLOY
        self.current_player = PLAYER1
        self.verbose = verbose

        # Salva lo stato iniziale per reset()
        self._initial_state = [(t.owner, t.units_stored) for t in self.mappa]

        # Truppe ancora da piazzare nella fase deploy del PLAYER
        self._deploy_pool = self.calculate_reinforcements(PLAYER1)
        self._deploy_territories = [t for t in self.mappa if t.get_owner() == PLAYER1]
        self._deploy_index = 0

    #ciclo di vita del gioco
    def reset(self):
        for t, (owner, units) in zip(self.mappa, self._initial_state):
            t.owner = owner
            t.units_stored = units
        self.current_player = PLAYER1
        self.phase = PHASE_DEPLOY
        self._deploy_pool = self.calculate_reinforcements(PLAYER1)
        self._deploy_territories = [t for t in self.mappa if t.get_owner() == PLAYER1]
        self._deploy_index = 0
        return self.get_state()

    def _start_deploy_phase(self, player):
        self._deploy_pool = self.calculate_reinforcements(player)
        self._deploy_territories = [t for t in self.mappa if t.get_owner() == player]

    def get_legal_actions(self, player):
        if self.phase == PHASE_DEPLOY:
            if self._deploy_index >= len(self._deploy_territories):
                return [("deploy", None, 0)]  # segnale di fine deploy
            t = self._deploy_territories[self._deploy_index]
            return [("deploy", t, amount) for amount in range(0, self._deploy_pool + 1)]

        if self.phase == PHASE_ACTION:
            return self._build_action_options(owner=player)

        return []

    def _build_action_options(self, owner):
        actions = [("pass",)]
        for t in self.mappa:
            if t.get_owner() != owner or t.get_units_stored() <= 1:
                continue
            max_t = t.get_units_stored() - 1
            for neighbor in t.get_neighbors():
                options = troop_options(max_t)
                if neighbor.get_owner() != owner:
                    actions.extend(("attack", t, neighbor, troops) for troops in options)
                else:
                    actions.extend(("move", t, neighbor, troops) for troops in options)
        return actions


    def step(self, action, player):
        action_type = action[0]
        if player != self.current_player:
            return self.get_state(), -10, False
        if self.phase == PHASE_DEPLOY:
            return self._step_deploy(action_type, action)
        if self.phase == PHASE_ACTION:
            return self._step_action(action_type, action)
        return self.get_state(), -10, False

    def _step_deploy(self, action_type, action):
        if action_type != "deploy":
            return self.get_state(), -10, False
        _, territory, amount = action
        if amount < 0 or amount > self._deploy_pool:
            return self.get_state(), -10, False
        if territory is not None:
            if territory.get_owner() != self.current_player:
                return self.get_state(), -10, False
            territory.add_units(amount)
            self._deploy_pool -= amount
        self._deploy_index += 1
        if self._deploy_index >= len(self._deploy_territories) or self._deploy_pool == 0:
            self.force_action_phase()
        return self.get_state(), 0, False

    def _step_action(self, action_type, action):
        acting_player = self.current_player
        if action_type == "attack":
            _, attacker, defender, troops = action
            if attacker.get_owner() != acting_player:
                return self.get_state(), -10, False
            if not attack(attacker, defender, troops):
                if self.verbose:
                    print(f"[{self.current_player}] Invalid attack.")
                return self.get_state(), -10, False
            if self.verbose:
                if defender.get_owner() == acting_player:
                    print(f"[{self.current_player}] Attacked {defender.get_name()} with {troops} troops -> Territory conquered!")
                else:
                    print(f"[{self.current_player}] Attacked {defender.get_name()} with {troops} troops -> "
                          f"Attack failed. Enemy holds with {defender.get_units_stored()} units.")

        elif action_type == "move":
            _, source, destination, troops = action
            if source.get_owner() != acting_player:
                return self.get_state(), -10, False
            if not move_troops(source, destination, troops):
                if self.verbose:
                    print(f"[{self.current_player}] Invalid move.")
                return self.get_state(), -10, False
            if self.verbose:
                print(f"[{self.current_player}] Moved {troops} troops from {source.get_name()} to {destination.get_name()}.")

        elif action_type == "pass":
            if self.verbose:
                print(f"[{self.current_player}] No action taken.")

        else:
            return self.get_state(), -10, False

        end_state = self._check_and_report_end(acting_player)
        if end_state is not None:
            return end_state

        self.current_player = self._switch_players(acting_player)
        self.phase = PHASE_DEPLOY
        self._start_deploy_phase(self.current_player)
        self._deploy_index = 0

        return self.get_state(), self.calculate_reward(acting_player), False

    def _switch_players(self, player):
        if player == PLAYER1:
            return PLAYER2
        return PLAYER1

    def _check_and_report_end(self, player):
        winner = self.check_game_over()
        if winner is None:
            return None
        opponent = self._switch_players(player)
        if winner == player:
            return self.get_state(), 100, True
        if winner == opponent:
            return self.get_state(), -100, True
        return None

    # Stato e reward

    #ritorna i territori con il loro owner e quante truppe hanno
    def get_state(self):
        state = []
        for territory in self.mappa:
            state.append(territory.get_owner())
            state.append(territory.get_units_stored())
        return state

    #serve per scambiare player1 e player2 (così la rete DQN pensa sempre di essere "player1"
    #anche quando la faccio giocare come player 2
    def get_swapped_state(self):
        swapped = []
        for val in self.get_state():
            if val == PLAYER1:
                swapped.append(PLAYER2)
            elif val == PLAYER2:
                swapped.append(PLAYER1)
            else:
                swapped.append(val)
        return swapped

    #reward intermedia
    def calculate_reward(self, player):
        opponent = self._switch_players(player)
        my_t = sum(1 for t in self.mappa if t.get_owner() == player)
        opp_t = sum(1 for t in self.mappa if t.get_owner() == opponent)
        return my_t - opp_t

    def check_game_over(self):
        owners = {t.get_owner() for t in self.mappa}
        if PLAYER2 not in owners:
            return PLAYER1
        if PLAYER1 not in owners:
            return PLAYER2
        return None

    #gestione dei rinforzi e fasi

    def calculate_reinforcements(self, owner):
        return sum(t.get_units_produced() for t in self.mappa if t.get_owner() == owner)

    def get_deploy_pool(self):
        return self._deploy_pool

    def force_action_phase(self):
        self.phase = PHASE_ACTION
        self._deploy_index = 0