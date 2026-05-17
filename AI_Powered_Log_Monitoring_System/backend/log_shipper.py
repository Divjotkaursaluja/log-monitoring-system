import argparse
import os
import re
import time
from datetime import datetime

import requests


LEVEL_PATTERN = re.compile(r"\b(ERROR|WARNING|WARN|INFO)\b", re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?)"
)


def classify_severity(line: str) -> str:
    match = LEVEL_PATTERN.search(line)
    if match:
        level = match.group(1).upper()
        return "WARNING" if level == "WARN" else level

    upper_line = line.upper()
    if any(token in upper_line for token in ("EXCEPTION", "FAILED", "CRITICAL", "TRACEBACK")):
        return "ERROR"
    if any(token in upper_line for token in ("DUPLICATE", "RETRY", "TIMEOUT")):
        return "WARNING"
    return "INFO"


def extract_timestamp(line: str) -> str | None:
    match = TIMESTAMP_PATTERN.search(line)
    if not match:
        return None

    raw = match.group("timestamp").replace(" ", "T").replace(",", ".")
    try:
        return datetime.fromisoformat(raw).isoformat()
    except ValueError:
        return None


def build_payload(line: str, service_name: str) -> dict:
    return {
        "level": classify_severity(line),
        "message": line.strip(),
        "service_name": service_name,
        "timestamp": extract_timestamp(line),
    }


def follow_file(path: str, from_start: bool):
    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        if not from_start:
            log_file.seek(0, os.SEEK_END)

        while True:
            line = log_file.readline()
            if line:
                yield line
                continue

            current_position = log_file.tell()
            if current_position > os.path.getsize(path):
                log_file.seek(0)

            time.sleep(1)


def send_log(api_url: str, payload: dict):
    response = requests.post(api_url, json=payload, timeout=5)
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Continuously ship app.log lines to FastAPI.")
    parser.add_argument("--file", default="app.log", help="Path to the source app.log file.")
    parser.add_argument("--api-url", default="http://localhost:8001/api/logs")
    parser.add_argument("--service-name", default="civic-issue-system")
    parser.add_argument("--from-start", action="store_true", help="Send existing lines before tailing new logs.")
    args = parser.parse_args()

    print(f"Monitoring {args.file} and sending logs to {args.api_url}")

    for line in follow_file(args.file, args.from_start):
        if not line.strip():
            continue

        payload = build_payload(line, args.service_name)
        try:
            send_log(args.api_url, payload)
            print(f"sent {payload['level']}: {payload['message'][:100]}")
        except requests.RequestException as exc:
            print(f"failed to send log: {exc}")


if __name__ == "__main__":
    main()
