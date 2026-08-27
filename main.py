import os
import torch
from game import Game, HumanController, RandomController, DQNController, PLAYER1, PLAYER2, scenarios, PHASE_DEPLOY, \
    PHASE_ACTION
from RL import DQNagent

MODEL_PATH = "trained_models/DQN_vs_random/easy_dqn_weights.pth"

def load_agent(mappa, model_path = MODEL_PATH):
    agent = DQNagent(mappa)
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Non trovo i pesi allenati in '{model_path}'. "
            f"Esegui prima train.py per generarli."
        )
    state_dict = torch.load(model_path, map_location=agent.device)
    agent.online_network.load_state_dict(state_dict)
    agent.online_network.eval()
    agent.epsilon = 0.0  # niente esplorazione: l'AI gioca sempre la mossa migliore
    return agent

def choose_scenario():
    print("\nScegli la mappa:")
    print("1. Easy")
    print("2. Medium")
    print("3. Hard")
    print("4. Italy")
    scenario_by_choice = {"1": "easy", "2": "medium", "3": "hard", "4": "italy"}
    choice = input("> ").strip()
    if choice in scenario_by_choice:
        return scenario_by_choice[choice]
    print("Scelta non valida, riprovo.")
    return choose_scenario()

def choose_mode(mappa):
    print("\nScegli la modalità di gioco:")
    print("1. Umano vs Umano")
    print("2. Umano vs Random")
    print("3. Umano vs AI (DQN allenata)")

    choice = input("> ").strip()

    if choice == "1":
        return {PLAYER1: HumanController(), PLAYER2: HumanController()}
    if choice == "2":
        return {PLAYER1: HumanController(), PLAYER2: RandomController()}
    if choice == "3":
        agent = load_agent(mappa)
        print("AI caricata. Buona fortuna :))")
        return {PLAYER1: HumanController(), PLAYER2: DQNController(agent)}

    print("Scelta non valida, riprovo.")
    return choose_mode(mappa)

def print_board(game):
    print("\n==============================")
    print("         WORLD CONQUEST")
    print("==============================")
    for i, t in enumerate(game.mappa):
        print(f"{i}: {t.get_name()} | Owner: {t.get_owner()} | Units: {t.get_units_stored()}")

def report_winner(winner):
    if winner == PLAYER1:
        print("\nPLAYER 1 HA VINTO!")
    elif winner == PLAYER2:
        print("\nPLAYER 2 HA VINTO!")
    else:
        print("\nA strange game. The only winning move is not to play.")

def run_game(game, controllers):
    while True:
        p = game.current_player
        controller = controllers[p]
        show_board = isinstance(controller, HumanController) and (
                (game.phase == PHASE_DEPLOY and game._deploy_index == 0)
                or game.phase == PHASE_ACTION
        )
        if show_board:
            print_board(game)
        action = controller.choose_action(game, p)
        state, reward, done = game.step(action, p)
        winner = game.check_game_over()
        if winner is not None or done:
            return winner
        if isinstance(controller, HumanController) and game.current_player != p:
            input("\nPremi INVIO per continuare...")


def main():
    scenario = choose_scenario()
    world = scenarios.build_world(scenario)
    game = Game(world, verbose=True)
    controllers = choose_mode(game.mappa)

    winner = run_game(game, controllers)
    report_winner(winner)

if __name__ == "__main__":
    main()