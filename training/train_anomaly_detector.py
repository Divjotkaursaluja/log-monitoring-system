import numpy as np
from sklearn.ensemble import IsolationForest

from ai_engine.model_store import save_model


def train():
    windows = np.array(
        [
            [0, 0, 1],
            [1, 0, 4],
            [1, 1, 8],
            [2, 1, 12],
            [2, 2, 18],
            [3, 2, 25],
            [4, 3, 35],
            [5, 4, 45],
            [8, 6, 70],
            [20, 12, 120],
        ],
        dtype=float,
    )
    model = IsolationForest(contamination=0.2, random_state=42)
    model.fit(windows)
    return save_model(model, "anomaly_detector.pkl")


if __name__ == "__main__":
    path = train()
    print(f"Saved anomaly detector model to {path}")
