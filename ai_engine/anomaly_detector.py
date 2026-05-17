import numpy as np
from sklearn.ensemble import IsolationForest

from ai_engine.model_store import load_model


class AnomalyDetector:
    def __init__(self, model=None):
        self.model = model or load_model("anomaly_detector.pkl") or self._build_baseline_model()

    def predict(self, error_count: int, warning_count: int, service_log_count: int) -> tuple[bool, float]:
        features = np.array([[error_count, warning_count, service_log_count]], dtype=float)
        prediction = int(self.model.predict(features)[0])
        score = float(self.model.decision_function(features)[0])
        return prediction == -1, score

    def _build_baseline_model(self):
        normal_windows = np.array(
            [
                [0, 0, 1],
                [1, 0, 4],
                [1, 1, 7],
                [2, 1, 10],
                [2, 2, 16],
                [3, 2, 22],
                [4, 3, 30],
                [5, 4, 45],
            ],
            dtype=float,
        )
        return IsolationForest(contamination=0.15, random_state=42).fit(normal_windows)
