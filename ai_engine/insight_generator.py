def generate_insight(category: str, severity: str, is_anomaly: bool, service_name: str) -> str:
    if is_anomaly:
        return (
            f"Anomalous log pattern detected in {service_name}. "
            f"The latest log is classified as {category} with {severity} severity."
        )

    if severity == "HIGH":
        return f"High severity {category} detected in {service_name}. Immediate review is recommended."

    if severity == "MEDIUM":
        return f"{category} detected in {service_name}. Monitor for repeated failures."

    return f"Log classified as {category} in {service_name}."
