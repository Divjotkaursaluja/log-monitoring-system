from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ai_engine.model_store import load_model
from ai_engine.preprocessing import build_text_features
from ai_engine.training_data import TRAINING_LOGS


class LogClassifier:
    def __init__(self, model=None):
        self.model = model or load_model("log_classifier.pkl") or self._build_baseline_model()

    def predict(self, level: str, message: str, service_name: str) -> tuple[str, float | None]:
        text = build_text_features(level, message, service_name)
        prediction = str(self.model.predict([text])[0])
        confidence = None

        if hasattr(self.model, "predict_proba"):
            confidence = float(max(self.model.predict_proba([text])[0]))

        return prediction, confidence

    def _build_baseline_model(self):
        samples = [build_text_features("ERROR", message, "baseline-service") for message, _ in TRAINING_LOGS]
        labels = [label for _, label in TRAINING_LOGS]
        model = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("classifier", MultinomialNB()),
            ]
        )
        return model.fit(samples, labels)
