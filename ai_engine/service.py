from ai_engine.anomaly_detector import AnomalyDetector
from ai_engine.classifier import LogClassifier
from ai_engine.insight_generator import generate_insight
from ai_engine.schemas import AIAnalysisResult, LogContext, NormalizedLog
from ai_engine.severity_predictor import SeverityPredictor


class AIAnalysisService:
    def __init__(
        self,
        classifier: LogClassifier | None = None,
        anomaly_detector: AnomalyDetector | None = None,
        severity_predictor: SeverityPredictor | None = None,
        model_version: str = "baseline-v1",
    ):
        self.classifier = classifier or LogClassifier()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.severity_predictor = severity_predictor or SeverityPredictor()
        self.model_version = model_version

    def analyze_log(self, log: NormalizedLog, context: LogContext | None = None) -> AIAnalysisResult:
        context = context or LogContext()
        category, confidence = self.classifier.predict(log.level, log.message, log.service_name)
        severity = self.severity_predictor.predict(log.level, category, log.message)
        is_anomaly, anomaly_score = self.anomaly_detector.predict(
            context.error_count,
            context.warning_count,
            context.service_log_count,
        )
        insight = generate_insight(category, severity, is_anomaly, log.service_name)
        
        print("Running NLP/ML pipeline...")
        print("Original log:", log.message)
        print("Predicted category:", category)
        print("Predicted severity:", severity)
        print("Anomaly:", is_anomaly)
        print("Confidence:", confidence)
        print("Anomaly score:", anomaly_score)

        return AIAnalysisResult(
            predicted_category=category,
            predicted_severity=severity,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            confidence=confidence,
            insight=insight,
            model_version=self.model_version,
        )
