import os

from train_dqn import train, evaluate, model_path_for, self_model_path_for

SEEDS = [0, 1, 2, 3, 4]
REFERENCE_SEED = SEEDS[0]  # seed usato per generare l'avversario fisso del self-play
EVAL_EPISODES = 300
EVAL_SEED_OFFSET = 1000  # seed di valutazione = seed di training + offset (mai uguali)

SCENARIOS = ["easy", "medium", "hard", "italy"]

HPARAMS_VS_RANDOM = {
    "easy":   dict(n_episodes=1000,  max_steps=400, learn_every=20,  gamma=0.95, batch_size=32, learning_rate=0.001,  epsilon_decay=0.995,  epsilon_min=0.01, target_update_rate=4000, mem_cap=9000, max_nxt_actions=64),
    "medium": dict(n_episodes=2500,  max_steps=400, learn_every=30,  gamma=0.97, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9977, epsilon_min=0.01, target_update_rate=12000, mem_cap=10000, max_nxt_actions=64),
    "hard":   dict(n_episodes=5500,  max_steps=500, learn_every=50,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9995, epsilon_min=0.01, target_update_rate=20000, mem_cap=15000, max_nxt_actions=64),
    "italy":  dict(n_episodes=2000,  max_steps=400, learn_every=25,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.998,  epsilon_min=0.01, target_update_rate=10000, mem_cap=9000, max_nxt_actions=64),
}

HPARAMS_SELF = {
    "easy":   dict(n_episodes=10000, max_steps=500, learn_every=40,  gamma=0.95, batch_size=32, learning_rate=0.001,  epsilon_decay=0.999,  epsilon_min=0.05, target_update_rate=16000, mem_cap=9000, max_nxt_actions=64),
    "medium": dict(n_episodes=20000, max_steps=600, learn_every=60,  gamma=0.97, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9999, epsilon_min=0.05, target_update_rate=24000, mem_cap=15000, max_nxt_actions=64),
    "hard":   dict(n_episodes=20000, max_steps=1200, learn_every=60, gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9999, epsilon_min=0.05, target_update_rate=24000, mem_cap=20000, max_nxt_actions=64),
    "italy":  dict(n_episodes=10000, max_steps=500, learn_every=50,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9997, epsilon_min=0.05, target_update_rate=20000, mem_cap=15000, max_nxt_actions=64),
}


def run_vs_random(scenario):
    hp = HPARAMS_VS_RANDOM[scenario]
    for seed in SEEDS:
        save_path = model_path_for(scenario, seed=seed)
        train(scenario=scenario, seed=seed, opponent_type="random", save_path=save_path, **hp)
        evaluate(scenario, agent_weights_path=save_path,
                 n_episodes=EVAL_EPISODES, seed=seed + EVAL_SEED_OFFSET)


def run_self_play(scenario):
    reference_opponent = model_path_for(scenario, seed=REFERENCE_SEED)
    if not os.path.exists(reference_opponent):
        raise FileNotFoundError(
            f"Manca l'avversario di riferimento per il self-play: {reference_opponent}. "
            f"Esegui prima run_vs_random('{scenario}') (serve il seed={REFERENCE_SEED})."
        )
    hp = HPARAMS_SELF[scenario]
    for seed in SEEDS:
        save_path = self_model_path_for(scenario, seed=seed)
        train(scenario=scenario, seed=seed, opponent_type="self",
              opp_weigths_path=reference_opponent, save_path=save_path, **hp)
        evaluate(scenario, agent_weights_path=save_path, opp_weigths_path=reference_opponent,
                 n_episodes=EVAL_EPISODES, seed=seed + EVAL_SEED_OFFSET)

if __name__ == "__main__":
    hp_hard = HPARAMS_VS_RANDOM["hard"]
    save_path = model_path_for("hard", seed=4)
    reference_opponent = model_path_for("hard", seed=REFERENCE_SEED)
    train(scenario="hard", seed=4, opponent_type="self", opp_weigths_path=reference_opponent, save_path=save_path, **hp_hard)
    evaluate("hard", agent_weights_path=save_path, n_episodes=EVAL_EPISODES, seed=4 + EVAL_SEED_OFFSET)
    run_self_play("italy")

# if __name__ == "__main__":
#     for scenario in SCENARIOS:
#         run_vs_random(scenario)
#     for scenario in SCENARIOS:
#         run_self_play(scenario)

# if __name__ == "__main__":
#     # resume: hard vs random da seed 3 (seed 0,1,2 già completati)
#     hp_hard = HPARAMS_VS_RANDOM["hard"]
#     for seed in [3, 4]:
#         save_path = model_path_for("hard", seed=seed)
#         train(scenario="hard", seed=seed, opponent_type="random",
#               save_path=save_path, **hp_hard)
#         evaluate("hard", agent_weights_path=save_path,
#                  n_episodes=EVAL_EPISODES, seed=seed + EVAL_SEED_OFFSET)
#
#     # italy vs random non ancora iniziato: tutti e 5 i seed
#     run_vs_random("italy")
#
#     # self-play: presuppone che vs_random sia completo per ogni scenario
#     # (easy/medium già finiti prima, hard/italy dopo i due blocchi sopra)
#     for scenario in ["easy", "medium", "hard", "italy"]:
#         run_self_play(scenario)

# if __name__ == "__main__":
#     #run_vs_random("hard")
#     for scenario in ["italy", "hard"]:
#         run_self_play(scenario)