from datetime import datetime

from pydantic import BaseModel


class NormalizedLog(BaseModel):
    level: str
    message: str
    service_name: str
    timestamp: datetime | None = None


class LogContext(BaseModel):
    error_count: int = 0
    warning_count: int = 0
    service_log_count: int = 0


class AIAnalysisResult(BaseModel):
    predicted_category: str
    predicted_severity: str
    is_anomaly: bool
    anomaly_score: float | None = None
    confidence: float | None = None
    insight: str
    model_version: str = "baseline-v1"
