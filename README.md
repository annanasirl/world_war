Turn-based territorial conquest game (Risiko-style) with a fully symmetric game engine and a Deep Q-Network agent trained to play it.

Built for Symbolic and Evolutionary Artificial Intelligence project.

-4 maps: easy (8 territories), medium (41), hard (22), italy (20 regions)
-symmetric engine; PLAYER1 and PLAYER2 follow the exact same rules with no player/enemy distinction
-3 modes: human vs human, human vs random bot, human vs trained DQN agent
-DQN agent with state-action value network, replay memory, target network, epsilon-greedy with decay
-probabilistic combat: attack outcome depends on the attacker/defender troop ratio

Status:
V symmetric engine working (easy, medium tested)
V first successful training run on easy (DQN Agent vs Random Bot)(improvements can be made)
X medium training in progress, still being tuned
X hard and italy not playable yet 
