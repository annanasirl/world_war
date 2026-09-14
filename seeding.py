import random

import numpy as np
import torch


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # Il progetto gira su CPU (DQNagent.device = torch.device("cpu")), quindi
    # le operazioni sono già deterministiche di default. Queste due righe
    # blindano la riproducibilità anche nel caso in futuro si passi a GPU.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False