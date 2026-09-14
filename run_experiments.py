import os

from train import train, evaluate, model_path_for, self_model_path_for

SEEDS = [0, 1, 2, 3, 4]
REFERENCE_SEED = SEEDS[0]  # seed usato per generare l'avversario fisso del self-play
EVAL_EPISODES = 300
EVAL_SEED_OFFSET = 1000  # seed di valutazione = seed di training + offset (mai uguali)

SCENARIOS = ["easy", "medium", "hard", "italy"]

HPARAMS_VS_RANDOM = {
    "easy":   dict(n_episodes=1000,  max_steps=400, learn_every=20,  gamma=0.95, batch_size=32, learning_rate=0.001,  epsilon_decay=0.995,  epsilon_min=0.01, target_update_rate=50),
    "medium": dict(n_episodes=2500,  max_steps=400, learn_every=30,  gamma=0.97, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9977, epsilon_min=0.01, target_update_rate=50),
    "hard":   dict(n_episodes=5500,  max_steps=500, learn_every=50,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9995, epsilon_min=0.01, target_update_rate=100),
    "italy":  dict(n_episodes=2000,  max_steps=400, learn_every=25,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.998,  epsilon_min=0.01, target_update_rate=100),
}

HPARAMS_SELF = {
    "easy":   dict(n_episodes=10000, max_steps=500, learn_every=40,  gamma=0.95, batch_size=32, learning_rate=0.001,  epsilon_decay=0.999,  epsilon_min=0.01, target_update_rate=50),
    "medium": dict(n_episodes=10000, max_steps=700, learn_every=60,  gamma=0.97, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9995, epsilon_min=0.01, target_update_rate=50),
    "hard":   dict(n_episodes=10000, max_steps=500, learn_every=100, gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9995, epsilon_min=0.01, target_update_rate=100),
    "italy":  dict(n_episodes=10000, max_steps=500, learn_every=50,  gamma=0.99, batch_size=64, learning_rate=0.0005, epsilon_decay=0.9995, epsilon_min=0.01, target_update_rate=100),
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
    for scenario in SCENARIOS:
        run_vs_random(scenario)
    for scenario in SCENARIOS:
        run_self_play(scenario)