import random
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim

from game import PLAYER1, PLAYER2, NONE

#costanti
ACTION_SPACE_SIZE = 7
STATE_SPACE_SIZE = 16
INPUT_SIZE = STATE_SPACE_SIZE + ACTION_SPACE_SIZE

#il gioco ci ritorna lo stato in un modo che la rete non può propriamente usare
#quindi questa funzione lo rende utilizzabile
def encode_state(state):
    owner_map = {PLAYER1: 1, PLAYER2: -1, NONE: 0}
    encoded = []
    for val in state:
        if isinstance(val, str):
            encoded.append(owner_map[val])
        else:
            encoded.append(val / 50.0) #boh #TODO: capire qui perchè avevo messo 50?
    return np.array(encoded, dtype=np.float32).reshape(1, -1)

#4 tipi di azioni tipo azione one hot coded,
# 1 numero x nazione da cui partono truppe e 1 n. per quello da cui arrivano e 1 n per il n di truppe inviate
#deploy 1 0 0 0 -1 nazione_in_cui_metti_i_soldati numero_di_soldati
#attack 0 1 0 0 attaccante difensore numero_di_soldati
#move 0 0 1 0 nazione_da_cui_partono_soldati nazione_in_cui_arrivano_i_soldati numero_di_soldati
#pass 0 0 0 1 -1 -1 -1
#per evitare che nei due numeri delle nazioni ci siano dei valori fuori scala NORMALZIZO INDICI DEI PAESI
#per evitare che NUMERO TRUPPE sia fuori scala NORMALIZZO

def encode_action(action, mappa, deploy_pool=None, territory_to_index=None):
    if territory_to_index is None:
        territory_to_index = {terr: i for i, terr in enumerate(mappa)}
    n = len(mappa)
    tipo = np.zeros(4, dtype=np.float32)
    source_idx = np.array([-1.0], dtype=np.float32)
    dest_idx = np.array([-1.0], dtype=np.float32)
    truppe = np.array([-1.0], dtype=np.float32)
    if action[0] == "deploy":
        tipo[0] = 1
        _, territory, amount = action
        if territory is not None:
            dest_idx[0] = territory_to_index[territory] / n
        pool = deploy_pool if deploy_pool else 0
        truppe[0] = (amount / pool) if pool > 0 else 0.0
    elif action[0] == "attack":
        tipo[1] = 1
        _, attacker, defender, troops = action
        source_idx[0] = territory_to_index[attacker] / n
        dest_idx[0] = territory_to_index[defender] / n
        truppe[0] = troops
    elif action[0] == "move":
        tipo[2] = 1
        _, source, destination, troops = action
        source_idx[0] = territory_to_index[source] / n
        dest_idx[0] = territory_to_index[destination] / n
        truppe[0] = troops
    else:  # pass
        tipo[3] = 1
    return np.concatenate([tipo, source_idx, dest_idx, truppe])

#classe per la replay memory
class ReplayMemory:
    def __init__(self, capacity = 9000):
        self.capacity = capacity
        self.buffer = []

    def push(self, state, action_idx, reward, next_state, done, next_legal_actions):
        if len(self.buffer) >= self.capacity:
            self.buffer.pop(0)
        self.buffer.append((state, action_idx, reward, next_state, done, next_legal_actions))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

#classe dqn per il network
class DQNnetwork(nn.Module):
    def __init__(self, input_size, output_size=1):
        super().__init__()

        self.network = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_size)
        )

    def forward(self, x):
        return self.network(x)

class DQNagent:
    def __init__(self, mappa, epsilon=1.0, gamma=0.95,
                 batch_size=32, learning_rate=0.001,
                 epsilon_decay=0.995, epsilon_min=0.05,
                 target_update_rate=50):
        self.mappa = mappa
        self.territory_to_idx = {terr: i for i, terr in enumerate(mappa)} #questo x velocizzare encode acton
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.gamma = gamma
        self.batch_size = batch_size
        self.target_update_rate = target_update_rate
        self.replay_memory = ReplayMemory()
        self.device = torch.device("cpu")
        self.state_space_size = 2 * len(mappa)
        self.action_space_size = ACTION_SPACE_SIZE
        self.input_size = self.state_space_size + self.action_space_size
        self.online_network = DQNnetwork(self.input_size).to(self.device)
        self.target_network = DQNnetwork(self.input_size).to(self.device)
        self._synch_target_network()
        self.optimizer = optim.Adam(self.online_network.parameters(), lr=learning_rate)
        self.loss_function = nn.MSELoss()

    #funzione per il decay di epsilon
    def decay_eps(self):
        self.epsilon = max(self.epsilon_min, self.epsilon_decay * self.epsilon)

    def encode_action_now(self, action, deploy_pool=None):
        return encode_action(action, self.mappa, deploy_pool=deploy_pool, territory_to_index=self.territory_to_idx)

    def encode_legal_actions_now(self, legal_actions, deploy_pool=None):
        return [encode_action(a, self.mappa, deploy_pool=deploy_pool, territory_to_index=self.territory_to_idx) for a in legal_actions]

    #FUNZIONE X inserire nella replay memory le tuple su cui allenare la rete
    def save_action_in_mem(self, state, action_vec, reward, next_state, done, next_legal_actions_vec):
        self.replay_memory.push(state, action_vec, reward, next_state, done, next_legal_actions_vec)

    #la funzione da chiamare ogni tot iterazione per risincronizzare la nwk online con quella target
    def _synch_target_network(self):
        self.target_network.load_state_dict(self.online_network.state_dict())

    def update_target_network(self, episode):
        if episode % self.target_update_rate == 0:
            self._synch_target_network()

    def _state_action_input(self, state, action):
        state_vec = encode_state(state).flatten()
        action_vec = encode_action(action, self.mappa, territory_to_index=self.territory_to_idx)
        x = np.concatenate([state_vec, action_vec])
        return torch.tensor(x, dtype=torch.float32, device=self.device)

    def choose_action(self, state, legal_actions, deploy_pool=None):
        if random.random() < self.epsilon:
            return random.choice(legal_actions)
        if len(legal_actions) == 1:
            return legal_actions[0]

        state_vec = encode_state(state).flatten()
        action_vecs = np.stack([encode_action(a, self.mappa, deploy_pool=deploy_pool, territory_to_index=self.territory_to_idx) for a in legal_actions])
        state_block = np.tile(state_vec, (len(legal_actions), 1))
        sa = np.concatenate([state_block, action_vecs], axis=1)
        sa_t = torch.tensor(sa, dtype=torch.float32, device=self.device)

        self.online_network.eval()
        with torch.no_grad():
            q_values = self.online_network(sa_t).squeeze(1)
        best_idx = torch.argmax(q_values).item()
        return legal_actions[best_idx]

    def learn(self):
        if len(self.replay_memory) < self.batch_size:
            return
        batch = self.replay_memory.sample(self.batch_size)
        states, actions, rewards, next_states, dones, next_legal_actions_list = zip(*batch)

        # ---- Q(s,a) predetta: UN SOLO forward pass per tutto il batch ----
        state_vecs = np.stack([encode_state(s).flatten() for s in states])
        sa = np.concatenate([state_vecs, np.stack(actions)], axis=1)
        sa_t = torch.tensor(sa, dtype=torch.float32, device=self.device)

        self.online_network.train()
        q_pred = self.online_network(sa_t).squeeze(1)  # shape (batch,)

        # ---- target: max_a' Q_target(s', a') per ogni sample ----
        # costruiamo UNA SOLA matrice con tutte le coppie (next_state, next_action)
        # di tutto il batch, così serve un solo forward pass sulla target network
        flat_rows = []
        counts = []
        for ns, next_actions in zip(next_states, next_legal_actions_list):
            if not next_actions:
                counts.append(0)
                continue
            ns_vec = encode_state(ns).flatten()
            for a in next_actions:
                a_vec = encode_action(a, self.mappa, territory_to_index=self.territory_to_idx)
                flat_rows.append(np.concatenate([ns_vec, a_vec]))
            counts.append(len(next_actions))

        self.target_network.eval()
        with torch.no_grad():
            if flat_rows:
                flat_t = torch.tensor(np.stack(flat_rows), dtype=torch.float32, device=self.device)
                all_q_next = self.target_network(flat_t).squeeze(-1)
            else:
                all_q_next = torch.tensor([], device=self.device)

        td_targets = torch.zeros(self.batch_size, dtype=torch.float32, device=self.device)
        idx = 0
        for i, (reward, done, count) in enumerate(zip(rewards, dones, counts)):
            if done or count == 0:
                td_targets[i] = reward
            else:
                max_q_next = all_q_next[idx: idx + count].max()
                td_targets[i] = reward + self.gamma * max_q_next
            idx += count

        loss = self.loss_function(q_pred, td_targets.detach())
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.online_network.parameters(), max_norm=1.0)
        self.optimizer.step()
        return loss.item()