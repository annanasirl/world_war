# World Conquest RL
 
Turn-based territorial conquest game (Risiko-style) with a fully symmetric game engine and a Deep Q-Network agent trained to play it.
 
**CURRENTLY STILL BUILDING** — project for *Symbolic and Evolutionary Artificial Intelligence*.
 
## Features
 
* 4 maps of increasing size and difficulty: **easy** (8 territories), **medium** (42), **italy** (20 regions), **hard** (87 territories, world map)
* Symmetric engine: `PLAYER1` and `PLAYER2` follow the exact same rules, no player/enemy distinction
* 3 playable modes: human vs human, human vs random bot, human vs trained DQN agent
* DQN agent: state-action value network, replay memory, target network, epsilon-greedy with decay
* Probabilistic combat: attack outcome depends on the attacker/defender troop ratio
* Training pipeline with seeding, self-play, structured result logging and statistical analysis

## Maps
 
| Map    | Territories | Starting territories per player | Notes |
|--------|:-----------:|:--------------------------------:|-------|
| easy   | 8           | 2                                 | continents, small board |
| medium | 42          | 3                                 | world map, regional split |
| italy  | 20          | 1                                 | Italian regions |
| hard   | 87          | 1                                 | full world map, huge board with a minimal starting foothold — the sparsity is what makes it "hard", not the rules |
 
## Game modes (`main.py`)
 
1. Human vs Human
2. Human vs Random bot
3. Human vs trained DQN agent (loads weights from `trained_models/`)

## Status
 
* V Symmetric engine working on all 4 maps
* V DQN vs random bot trained and evaluated on all 4 maps, multi-seed (5 seeds each)
* V Self-play training implemented and evaluated on all 4 maps — winrates are much more unstable and seed-dependent (especially on medium and italy), needs more tuning
* V Reproducible, logged, statistically-analyzed experiment pipeline (seeding, JSONL logs, CI + Welch's t-test)
* !! to be fixed: `main.py`'s human-vs-AI mode looks for weights in `run_experiments.py` (`trained_models/dqn_vs_random/<map>_dqn_weights_rand__seed0.pth`) only and needs to be reconciled 
* x SECOND ALGORITHM NEEDED FOR COMPARISON not implemented yet (already hooked into `analyze_results.py` for a future comparison)
* x Hyperparameter tuning still highly needed