import json
import os
from datetime import datetime, timezone


def log_run_result(log_path: str, **fields) -> None:
    """
    Aggiunge una riga di risultato al file di log (append; crea file e
    cartella se non esistono). Aggiunge automaticamente un timestamp UTC.

    Esempio:
        log_run_result(
            "results/training_log.jsonl",
            run_type="train", algorithm="dqn", scenario="easy",
            opponent_type="random", seed=0, final_winrate=0.87,
        )
    """
    directory = os.path.dirname(log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), **fields}
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_results(log_path: str) -> list:
    """Legge tutte le righe del log come lista di dict (nessuna dipendenza da pandas)."""
    if not os.path.exists(log_path):
        return []
    with open(log_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
