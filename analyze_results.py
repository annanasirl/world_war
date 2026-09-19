import math
from collections import defaultdict

from results_logging import load_results

CONFIDENCE_Z = 1.96  # ~95% per l'approssimazione normale (ok per n non piccolissimo)


def summarize(values):
    n = len(values)
    mean = sum(values) / n
    if n > 1:
        variance = sum((v - mean) ** 2 for v in values) / (n - 1)
        std = math.sqrt(variance)
        ci95 = CONFIDENCE_Z * std / math.sqrt(n)
    else:
        std, ci95 = float("nan"), float("nan")
    return {"n": n, "mean": mean, "std": std, "ci95": ci95}


def group_eval_winrates(eval_log_path="results/second_version/eval_log.jsonl"):
    """Ritorna {(algorithm, scenario, opponent_type): [winrate_seed0, winrate_seed1, ...]}."""
    records = load_results(eval_log_path)
    groups = defaultdict(list)
    for r in records:
        key = (r.get("algorithm"), r.get("scenario"), r.get("opponent_type"))
        groups[key].append(r["winrate"])
    return groups


def welch_ttest(sample_a, sample_b):
    """
    T-test di Welch (non assume varianze uguali) per confrontare due
    configurazioni, es. DQN vs REINFORCE sugli stessi (mappa, avversario).
    Richiede scipy; se non è installato ritorna solo un avviso.
    """
    try:
        from scipy import stats
    except ImportError:
        return {"t_stat": None, "p_value": None,
                "note": "scipy non installato: pip install scipy per calcolare il p-value"}
    t_stat, p_value = stats.ttest_ind(sample_a, sample_b, equal_var=False)
    return {"t_stat": t_stat, "p_value": p_value}


if __name__ == "__main__":
    groups = group_eval_winrates()

    if not groups:
        print("Nessun risultato trovato in results/eval_log.jsonl. "
              "Lancia prima run_experiments.py (o train.py/evaluate() direttamente).")
    else:
        print("Riepilogo winrate di evaluate() per (algoritmo, mappa, avversario):\n")
        for key, winrates in sorted(groups.items(), key=lambda kv: [str(x) for x in kv[0]]):
            s = summarize(winrates)
            algo, scenario, opp = key
            print(f"{str(algo):10s} | {str(scenario):8s} | vs {str(opp):6s} | "
                  f"n_seed={s['n']:2d} | winrate medio={s['mean']:.1%} ± {s['ci95']:.1%} (IC 95%)")

        # Esempio pronto per quando anche REINFORCE avrà scritto risultati sullo stesso log:
        dqn_group = groups.get(("dqn", "easy", "random"))
        reinforce_group = groups.get(("reinforce", "easy", "random"))
        if dqn_group and reinforce_group:
            print("\nDQN vs REINFORCE su 'easy' vs random:", welch_ttest(dqn_group, reinforce_group))

