HIGH_RISK_CATEGORIES = {"PAYMENT_ERROR", "DATABASE_ERROR", "SECURITY_THREAT"}
MEDIUM_RISK_CATEGORIES = {"LOGIN_ERROR", "API_ERROR"}


class SeverityPredictor:
    def predict(self, level: str, category: str, message: str) -> str:
        normalized_level = level.upper().strip()
        normalized_message = message.upper()

        if normalized_level in {"CRITICAL", "ERROR"}:
            return "HIGH"

        if any(token in normalized_message for token in ("DEADLOCK", "REFUSED", "FAILED", "TIMEOUT")):
            return "HIGH"

        if category in HIGH_RISK_CATEGORIES:
            return "HIGH"

        if category in MEDIUM_RISK_CATEGORIES or normalized_level == "WARNING":
            return "MEDIUM"

        return "LOW"
