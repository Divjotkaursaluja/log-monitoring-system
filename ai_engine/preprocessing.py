import re


def clean_log_message(message: str) -> str:
    normalized = message.lower()
    normalized = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", " ip_address ", normalized)
    normalized = re.sub(r"\b[0-9a-f]{8,}\b", " hex_id ", normalized)
    normalized = re.sub(r"\d+", " number ", normalized)
    normalized = re.sub(r"[^a-zA-Z_ ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def build_text_features(level: str, message: str, service_name: str) -> str:
    return " ".join(
        [
            level.lower().strip(),
            service_name.lower().strip(),
            clean_log_message(message),
        ]
    ).strip()
