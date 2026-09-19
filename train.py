import os
import time
import torch

from game import Game, RandomController, PLAYER1, PLAYER2, PHASE_DEPLOY, scenarios, PHASE_ACTION, DQNController
from RL import DQNagent

from seeding import set_seed
from results_logging import log_run_result
#costanti
MODEL_PATH_RAND = "trained_models/third_version/dqn_vs_random"
MODEL_PATH_SELF = "trained_models/third_version/dqn_vs_self"

TRAIN_LOG_PATH = "results/third_version/training_log.jsonl"
EVAL_LOG_PATH = "results/third_version/eval_log.jsonl"
VERB_LOG_PATH = "results/third_version/verb_log.jsonl"

def model_path_for(scenario, seed=None):
    suffix = f"_seed{seed}" if seed is not None else ""
    return os.path.join(MODEL_PATH_RAND, f"{scenario}_dqn_weights_rand_{suffix}.pth")

def self_model_path_for(scenario, seed=None):
    suffix = f"_seed{seed}" if seed is not None else ""
    return os.path.join(MODEL_PATH_SELF, f"{scenario}_dqn_weights_self_{suffix}.pth")

def _perspective_state(game, player):
    return game.get_state() if player == PLAYER1 else game.get_swapped_state()

#l'avversario e sempre lo slot opposto a quello dell'agente in questo episodio
def play_opp_turn(game, opp_player, opp_controller, agent_player):
    state = game.get_state()
    while game.current_player == opp_player:
        action = opp_controller.choose_action(game, opp_player)
        state, _, done = game.step(action, opp_player)
        if done:
            break
    winner = game.check_game_over()
    if winner == opp_player:
        return state, -100, True
    if winner == agent_player:
        return state, 100, True
    return state, game.reward_for(agent_player), False

def load_other_agent(mappa, weigths_path, epsilon=0.0):
    opp_agent = DQNagent(mappa)
    state_dict = torch.load(weigths_path, map_location=opp_agent.device)
    opp_agent.online_network.load_state_dict(state_dict)
    opp_agent.online_network.eval()
    opp_agent.epsilon = epsilon
    return opp_agent

def train(scenario = "easy", n_episodes = 1000, max_steps=5000, opp_controller =None, learn_every = 1,
          gamma=0.95, batch_size=32, learning_rate=0.001, epsilon_decay=0.999, epsilon_min=0.01, target_update_rate=50, mem_cap=9000, max_nxt_actions=64,
          opp_weigths_path = None, save_path = None, seed=None, opponent_type=None, log_path=TRAIN_LOG_PATH, verb_log_path=VERB_LOG_PATH):
    if seed is not None:
        set_seed(seed)
    #creo mappa, il gioco e agent, setto il controller dell'opponente
    world = scenarios.build_world(scenario)
    game = Game(world)
    agent = DQNagent(game.mappa, gamma=gamma, batch_size=batch_size,
                        learning_rate=learning_rate,
                        epsilon_decay=epsilon_decay,
                        epsilon_min=epsilon_min,
                        target_update_rate=target_update_rate,
                        mem_capacity=mem_cap,
                        max_nxt_actions=max_nxt_actions)
    if opp_controller is None:
        if opp_weigths_path is not None:
            opp_agent = load_other_agent(game.mappa, opp_weigths_path)
            opp_controller = DQNController(opp_agent)
        else:
            opp_controller = RandomController()

    #path per salvare i pesi
    model_path = save_path or model_path_for(scenario)
    wins = 0
    losses = 0
    boh = 0
    steps_sum = 0
    turns_sum = 0
    territories_sum = 0
    p1wins = 0
    p2wins = 0

    # storico completo (un valore per episodio), serve solo per il riepilogo
    # finale/il log run-per-run
    outcome_history = []  # +1 vittoria, -1 sconfitta, 0 altro
    steps_history = []
    turns_history = []
    territories_history = []

    start_time = time.time()

    # inizio training per ogni episodio
    for episode in range(n_episodes):

        # agente gioca a episodi alterni come PLAYER1 e come PLAYER2
        # x imparare a giocare bene da entrambi i lati
        agent_player = PLAYER1 if episode % 2 == 0 else PLAYER2
        opp_player = PLAYER2 if agent_player == PLAYER1 else PLAYER1
        # faccio ripartire il gioco
        game.reset(starting_player=agent_player)
        done = False
        steps = 0
        turns = 0
        reward = 0

        # se agente fa PLAYER2, il gioco parte comunque con PLAYER1
        # cosi' fa sempre reset() e faccio giocare prima l'avversario
        if game.current_player == opp_player:
            _, reward, done = play_opp_turn(game, opp_player, opp_controller, agent_player)
        state = _perspective_state(game, agent_player)

        # while not condizioni di terminazione
        while not done and turns < max_steps:
            # ricordo in che fase eravamo prima di questa decisione: solo la
            # decisione presa in PHASE ACTION chiude un turno completo
            phase_before = game.phase
            # prendo le azioni possibili di agent_player
            legal_actions = game.get_legal_actions(agent_player)
            # se siamo nella fase di deploy devo inizializzare deploy pool
            deploy_pool = game.get_deploy_pool() if game.phase == PHASE_DEPLOY else None
            # scelgo l'azione tra le legal actions
            action = agent.choose_action(state, legal_actions, deploy_pool=deploy_pool)
            # faccio encoding dell'azione in modo che poi la DNN possa usarla
            action_vec = agent.encode_action_now(action, deploy_pool=deploy_pool)
            # eseguo l'azione e ricavo next_state, reward, done
            next_state, reward, done = game.step(action, agent_player)

            # se il turno dell'agente ha finito e il gioco non è finito devo prima
            # far giocare l'avversario
            # (se non vedo cosa fa l'avversario non posso scegliere la prox azione)
            if not done and game.current_player == opp_player:
                _, opp_reward, done = play_opp_turn(game, opp_player, opp_controller, agent_player)
                reward = opp_reward if done else reward + opp_reward
            next_state = _perspective_state(game, agent_player)
            # prendo le nuove azioni possibili (cambiano di turno in turno)
            next_legal_actions = [] if done else game.get_legal_actions(agent_player)
            next_deploy_pool = None
            if not done and game.phase == PHASE_DEPLOY:
                next_deploy_pool = game.get_deploy_pool()
            next_action_vecs = agent.encode_legal_actions_now(next_legal_actions, deploy_pool=next_deploy_pool)

            # salviamo l'azione nella replay memory
            agent.save_action_in_mem(state, action_vec, reward, next_state, done, next_action_vecs)

            # chiamo learn e poi vado avanti
            if steps % learn_every == 0:
                agent.learn()
            state = next_state
            steps += 1
            if phase_before == PHASE_ACTION:
                turns += 1

        winner = game.check_game_over()
        if winner == agent_player:
            wins += 1
            outcome_history.append(1)
            if agent_player == PLAYER1:
                p1wins += 1
            else:
                p2wins += 1
        elif winner == opp_player:
            losses += 1
            outcome_history.append(-1)
        else:
            boh += 1
            outcome_history.append(0)

        steps_sum += steps
        turns_sum += turns
        final_territories = sum(1 for t in game.mappa if t.get_owner() == agent_player)
        territories_sum += final_territories
        steps_history.append(steps)
        turns_history.append(turns)
        territories_history.append(final_territories)

        agent.decay_eps()
        agent.update_target_network(episode)
        if episode % 100 == 0:
            n = episode + 1 if episode < 100 else 100
            print(f"Episode {episode:4d} | Wins last 100: {wins} | Losses last 100: {losses} | "
                  f"Bohs last 100: {boh} | Epsilon: {agent.epsilon:.3f} | "
                  f"p1wins last 100: {p1wins} | p2wins: {p2wins} | "
                  f"Avg steps: {steps_sum / n:.0f} | Avg turns: {turns_sum / n:.0f} | "
                  f"Avg agent territories at end: {territories_sum / n:.1f}")
            log_run_result(
                verb_log_path, run_type="train", algorithm="dqn", scenario=scenario, opponent_type=opponent_type,
                seed=seed, episode=episode, wins=wins, losses=losses, boh=boh, p1wins=p1wins, p2wins=p2wins,
                avgsteps=(steps_sum / n), avgturns=(turns_sum / n), avgagentterritories=(territories_sum / n)
            )
            wins = 0
            losses = 0
            boh = 0
            steps_sum = 0
            turns_sum = 0
            territories_sum = 0
            p1wins = 0
            p2wins = 0

    train_time = time.time() - start_time

    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    torch.save(agent.online_network.state_dict(), model_path)
    print(f"pesi salvati in {model_path}")

    # ---- riepilogo del run + log su file, per l'analisi statistica multi-seed ----
    window = min(500, n_episodes)
    final_outcomes = outcome_history[-window:]
    final_winrate = sum(1 for o in final_outcomes if o == 1) / len(final_outcomes)
    overall_winrate = sum(1 for o in outcome_history if o == 1) / len(outcome_history)

    log_run_result(
        log_path,
        run_type="train",
        algorithm="dqn",
        scenario=scenario,
        opponent_type=opponent_type,
        seed=seed,
        n_episodes=n_episodes,
        max_steps=max_steps,
        model_path=model_path,
        opp_weights_path=opp_weigths_path,
        hyperparams=dict(
            gamma=gamma, batch_size=batch_size, learning_rate=learning_rate,
            epsilon_decay=epsilon_decay, epsilon_min=epsilon_min,
            target_update_rate=target_update_rate, learn_every=learn_every, mem_capacity=mem_cap, max_nxt_actions=max_nxt_actions
        ),
        train_time_seconds=round(train_time, 1),
        final_winrate=round(final_winrate, 4),
        final_window_size=len(final_outcomes),
        overall_winrate=round(overall_winrate, 4),
        avg_steps_final_window=round(sum(steps_history[-window:]) / len(steps_history[-window:]), 1),
        avg_turns_final_window=round(sum(turns_history[-window:]) / len(turns_history[-window:]), 1),
        avg_territories_final_window=round(sum(territories_history[-window:]) / len(territories_history[-window:]), 2),
    )
    return agent

def evaluate(scenario, agent_weights_path, opp_weigths_path=None, n_episodes=300, max_steps=1000,
             seed=None, log_path=EVAL_LOG_PATH):
    if seed is not None:
        set_seed(seed)
    world = scenarios.build_world(scenario)
    game = Game(world)

    agent = load_other_agent(game.mappa, agent_weights_path, epsilon=0.0)
    agent_controller = DQNController(agent)

    if opp_weigths_path is not None:
        opp_agent = load_other_agent(game.mappa, opp_weigths_path, epsilon=0.0)
        opp_controller = DQNController(opp_agent)
    else:
        opp_controller = RandomController()

    wins = losses = boh = 0
    outcome_history = []
    start_time = time.time()
    for episode in range(n_episodes):
        agent_player = PLAYER1 if episode % 2 == 0 else PLAYER2
        opp_player = PLAYER2 if agent_player == PLAYER1 else PLAYER1
        game.reset(starting_player=agent_player)
        done = False
        reward = 0
        turns = 0

        if game.current_player == opp_player:
            _, reward, done = play_opp_turn(game, opp_player, opp_controller, agent_player)

        while not done and turns < max_steps:
            phase_before = game.phase
            action = agent_controller.choose_action(game, agent_player)
            _, reward, done = game.step(action, agent_player)
            if not done and game.current_player == opp_player:
                _, reward, done = play_opp_turn(game, opp_player, opp_controller, agent_player)
            if phase_before == PHASE_ACTION:
                turns += 1

        winner = game.check_game_over()
        if winner == agent_player:
            wins += 1
            outcome_history.append(1)
        elif winner == opp_player:
            losses += 1
            outcome_history.append(-1)
        else:
            boh += 1
            outcome_history.append(0)
    eval_time = time.time() - start_time

    opp_name = "Random" if opp_weigths_path is None else os.path.basename(opp_weigths_path)
    winrate = wins / n_episodes
    print(f"[{scenario}] {os.path.basename(agent_weights_path)} vs {opp_name} | "
          f"Wins: {wins}/{n_episodes} | Losses: {losses} | Boh: {boh} | "
          f"Winrate: {winrate:.1%}")

    log_run_result(
        log_path,
        run_type="eval",
        algorithm="dqn",
        scenario=scenario,
        opponent_type="random" if opp_weigths_path is None else "self",
        seed=seed,
        n_episodes=n_episodes,
        max_steps=max_steps,
        agent_weights_path=agent_weights_path,
        opp_weights_path=opp_weigths_path,
        wins=wins,
        losses=losses,
        boh=boh,
        winrate=round(winrate, 4),
        eval_time_seconds=round(eval_time, 1),
    )

    return wins, losses, boh