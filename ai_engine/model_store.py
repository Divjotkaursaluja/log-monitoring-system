from pathlib import Path
from typing import Any

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"


def model_path(filename: str) -> Path:
    return MODEL_DIR / filename


def load_model(filename: str) -> Any | None:
    path = model_path(filename)
    if not path.exists():
        return None
    return joblib.load(path)


def save_model(model: Any, filename: str) -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = model_path(filename)
    joblib.dump(model, path)
    return path
