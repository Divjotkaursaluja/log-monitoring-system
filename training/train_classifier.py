from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from ai_engine.model_store import save_model
from ai_engine.preprocessing import build_text_features
from ai_engine.training_data import TRAINING_LOGS


def train():
    samples = [build_text_features("ERROR", message, "training-service") for message, _ in TRAINING_LOGS]
    labels = [label for _, label in TRAINING_LOGS]
    model = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("classifier", MultinomialNB()),
        ]
    )
    model.fit(samples, labels)
    return save_model(model, "log_classifier.pkl")


if __name__ == "__main__":
    path = train()
    print(f"Saved classifier model to {path}")
