from dataclasses import dataclass


HIGH_SEVERITIES = {"HIGH", "CRITICAL"}
MIN_ML_ALERT_CONFIDENCE = 0.25
SECURITY_KEYWORDS = {
    "UNAUTHORIZED",
    "SUSPICIOUS",
    "BRUTE FORCE",
    "INTRUSION",
    "BREACH",
    "ATTACK",
    "MALWARE",
    "TOKEN",
}


@dataclass
class AlertDecision:
    should_alert: bool
    alert_type: str
    severity: str
    category: str
    message: str
    notify_email: bool
    reasons: list[str]


def _is_security_keyword_match(message: str) -> bool:
    upper_message = message.upper()
    return any(keyword in upper_message for keyword in SECURITY_KEYWORDS)


def _recent_error_count(cursor, service_name: str) -> int:
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM logs
        WHERE service_name=%s
          AND level='ERROR'
          AND timestamp >= (CURRENT_TIMESTAMP - INTERVAL 5 MINUTE)
        """,
        (service_name,),
    )
    return cursor.fetchone()["total"]


def _recent_anomaly_count(cursor, service_name: str) -> int:
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM ai_log_analysis a
        JOIN logs l ON l.id = a.log_id
        WHERE l.service_name=%s
          AND a.is_anomaly = TRUE
          AND a.created_at >= (CURRENT_TIMESTAMP - INTERVAL 10 MINUTE)
        """,
        (service_name,),
    )
    return cursor.fetchone()["total"]


def evaluate_alert(cursor, log_id: int, level: str, message: str, service_name: str, analysis) -> AlertDecision:
    predicted_category = str(getattr(analysis, "predicted_category", "UNKNOWN"))
    predicted_severity = str(getattr(analysis, "predicted_severity", "LOW")).upper()
    is_anomaly = bool(getattr(analysis, "is_anomaly", False))
    confidence = getattr(analysis, "confidence", None)
    ml_confident = confidence is None or confidence >= MIN_ML_ALERT_CONFIDENCE
    category = predicted_category if ml_confident else "UNKNOWN"
    security_keyword_match = _is_security_keyword_match(message)
    recent_errors = _recent_error_count(cursor, service_name)
    recent_anomalies = _recent_anomaly_count(cursor, service_name)

    reasons = []
    if predicted_severity in HIGH_SEVERITIES and ml_confident:
        reasons.append("ML predicted high severity")
    if is_anomaly:
        reasons.append("ML anomaly detector flagged this log")
    if predicted_category.upper() == "SECURITY_THREAT" and ml_confident:
        category = "SECURITY_THREAT"
        reasons.append("ML classified this log as a security threat")
    if security_keyword_match:
        category = "SECURITY_THREAT"
        reasons.append("Security threat rule matched")
    if recent_errors >= 3:
        reasons.append(f"{recent_errors} ERROR logs in the last 5 minutes")
    if recent_anomalies >= 3:
        reasons.append(f"{recent_anomalies} anomalies in the last 10 minutes")

    should_alert = bool(reasons)
    alert_severity = "LOW"
    if "SECURITY_THREAT" == category or (predicted_severity in HIGH_SEVERITIES and ml_confident) or recent_anomalies >= 3:
        alert_severity = "CRITICAL"
    elif is_anomaly or recent_errors >= 3:
        alert_severity = "HIGH"
    elif predicted_severity == "MEDIUM":
        alert_severity = "MEDIUM"

    alert_type = "ML_INCIDENT" if should_alert else "NONE"
    if category == "SECURITY_THREAT":
        alert_type = "SECURITY_THREAT"
    elif recent_anomalies >= 3:
        alert_type = "REPEATED_ANOMALY"
    elif recent_errors >= 3:
        alert_type = "ERROR_BURST"
    elif is_anomaly:
        alert_type = "ANOMALY"
    elif predicted_severity in HIGH_SEVERITIES and ml_confident:
        alert_type = "HIGH_SEVERITY"

    return AlertDecision(
        should_alert=should_alert,
        alert_type=alert_type,
        severity=alert_severity,
        category=category,
        message=f"{'; '.join(reasons)}: {message}" if reasons else message,
        notify_email=alert_severity == "CRITICAL" or category == "SECURITY_THREAT" or recent_anomalies >= 3,
        reasons=reasons,
    )


def save_alert(cursor, log_id: int, service_name: str, decision: AlertDecision) -> int:
    cursor.execute(
        """
        INSERT INTO alerts (
            log_id,
            alert_type,
            severity,
            category,
            message,
            status,
            acknowledged,
            resolved,
            source_service
        )
        VALUES (%s, %s, %s, %s, %s, 'OPEN', FALSE, FALSE, %s)
        """,
        (
            log_id,
            decision.alert_type,
            decision.severity,
            decision.category,
            decision.message,
            service_name,
        ),
    )
    return cursor.lastrowid
