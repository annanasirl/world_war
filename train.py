import os
import torch

from game import Game, RandomController, PLAYER1, PLAYER2, PHASE_DEPLOY, scenarios
from RL import DQNagent

#costanti
MODEL_PATH = "./trained_models/"

def model_path_for(scenario):
    return os.path.join(MODEL_PATH, f"{scenario}_dqn_weights_1.pth")

#PER SEMPLICITÀ ALLENO L'AI COME PLAYER 1
def play_opp_turn(game, opp_player, opp_controller):
    state = game.get_state()
    while game.current_player == opp_player:
        action = opp_controller.choose_action(game, opp_player)
        state, _, done = game.step(action, opp_player)
        if done:
            break
    winner = game.check_game_over()
    if winner == PLAYER2:
        return state, -100, True
    if winner == PLAYER1:
        return state, 100, True
    return state, game.calculate_reward(PLAYER1), False

def train(scenario = "easy", n_episodes = 1000, MAX_STEPS=5000, opp_controller =None, learn_every = 1):
    #creo mappa, il gioco e agent, setto il controller dell'opponente
    world = scenarios.build_world(scenario)
    game = Game(world)
    agent = DQNagent(game.mappa)
    if opp_controller is None:
        opp_controller = RandomController()

    #path per salvare i pesi
    model_path = model_path_for(scenario)
    wins = 0
    losses = 0
    boh = 0
    steps_sum = 0
    territories_sum = 0

    #inizio training per ogni episodio
    for episode in range(n_episodes):
        #faccio ripartire il gioco
        state = game.reset()
        done = False
        steps = 0
        reward = 0

        #while not condizioni di terminazione
        while not done and steps < MAX_STEPS:
            #prendo le azioni possibili di PLAYER1
            legal_actions = game.get_legal_actions(PLAYER1)
            #se siamo nella fase di deploy devo inizializzare deploy pool
            deploy_pool = game.get_deploy_pool() if game.phase == PHASE_DEPLOY else None
            #scelgo l'azione tra le legal actions
            action = agent.choose_action(state, legal_actions, deploy_pool=deploy_pool)
            #faccio encoding dell'azione in modo che poi la DNN possa usarla
            action_vec = agent.encode_action_now(action, deploy_pool=deploy_pool)
            #eseguo l'azione e ricavo next_state, reward, done
            next_state, reward, done = game.step(action, PLAYER1)

            #se il turno dell'agente ha finito e il gioco non è finito devo prima
            #far giocare l'avversario
            #(se non vedo cosa fa l'avversario non posso scegliere la prox azione)
            if not done and game.current_player == PLAYER2:
                next_state, reward, done = play_opp_turn(game, PLAYER2, opp_controller)
            #prendo le nuove azioni possibili (cambiano di turno in turno)
            next_legal_actions = [] if done else game.get_legal_actions(PLAYER1)
            next_deploy_pool = None
            if not done and game.phase == PHASE_DEPLOY:
                next_deploy_pool = game.get_deploy_pool()
            next_action_vecs = agent.encode_legal_actions_now(next_legal_actions, deploy_pool=next_deploy_pool)

            #salviamo l'azione nella replay memory
            agent.save_action_in_mem(state, action_vec, reward, next_state, done, next_action_vecs)

            #chiamo learn e poi vado avanti
            if steps % learn_every == 0:
                agent.learn()
            state = next_state
            steps += 1
        if reward == 100:
            wins += 1
        elif reward == -100:
            losses += 1
        else:
            boh += 1

        steps_sum += steps
        territories_sum += sum(1 for t in game.mappa if t.get_owner() == PLAYER1)

        agent.decay_eps()
        agent.update_target_network(episode)
        if episode % 100 == 0:
            n = episode + 1 if episode < 100 else 100
            print(f"Episode {episode:4d} | Wins last 100: {wins} | Losses last 100: {losses} | "
                  f"Bohs last 100: {boh} | Epsilon: {agent.epsilon:.3f} | "
                  f"Avg steps: {steps_sum / n:.0f} | Avg PLAYER1 territories at end: {territories_sum / n:.1f}")
            wins = 0
            losses = 0
            boh = 0
            steps_sum = 0
            territories_sum = 0

    os.makedirs(MODEL_PATH, exist_ok=True)
    torch.save(agent.online_network.state_dict(), model_path)
    print(f"pesi salvati in {model_path}")
    return agent

#TODO: fix performance issue for training on medium
if __name__ == "__main__":
    train(scenario="medium", n_episodes=200,learn_every=10)
