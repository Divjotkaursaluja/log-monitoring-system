from collections import Counter
from datetime import datetime, timezone

import mysql.connector
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "log_monitor",
}

KNOWN_LEVELS = {"ERROR", "WARNING", "INFO"}

app = FastAPI(title="AI Powered Log Monitoring System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LogIn(BaseModel):
    level: str | None = None
    message: str = Field(..., min_length=1)
    service_name: str = Field(default="civic-issue-system", min_length=1)
    timestamp: datetime | None = None


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def classify_severity(message: str, level: str | None = None) -> str:
    normalized_level = (level or "").strip().upper()
    if normalized_level in KNOWN_LEVELS:
        return normalized_level

    text = message.upper()
    if any(token in text for token in ("ERROR", "EXCEPTION", "FAILED", "CRITICAL", "TRACEBACK")):
        return "ERROR"
    if any(token in text for token in ("WARNING", "WARN", "DUPLICATE", "RETRY", "TIMEOUT")):
        return "WARNING"
    return "INFO"


def serialize_log(row):
    timestamp = row.get("timestamp")
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()

    return {
        "id": row.get("id"),
        "level": classify_severity(row.get("message", ""), row.get("level")),
        "message": row.get("message", ""),
        "service_name": row.get("service_name", "unknown-service"),
        "timestamp": timestamp,
    }


def fetch_logs(limit: int = 100):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, level, message, service_name, timestamp
        FROM logs
        ORDER BY timestamp DESC, id DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [serialize_log(row) for row in rows]


@app.get("/api/health")
def health():
    return {"status": "healthy", "checked_at": datetime.now(timezone.utc).isoformat()}


@app.post("/api/logs", status_code=201)
def add_log(log: LogIn):
    level = classify_severity(log.message, log.level)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if log.timestamp:
            cursor.execute(
                """
                INSERT INTO logs (level, message, service_name, timestamp)
                VALUES (%s, %s, %s, %s)
                """,
                (level, log.message, log.service_name, log.timestamp),
            )
        else:
            cursor.execute(
                """
                INSERT INTO logs (level, message, service_name)
                VALUES (%s, %s, %s)
                """,
                (level, log.message, log.service_name),
            )
        conn.commit()
        return {"message": "Log stored successfully", "level": level}
    except mysql.connector.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        cursor.close()
        conn.close()


@app.get("/api/logs")
def get_logs(limit: int = Query(default=100, ge=1, le=500)):
    return fetch_logs(limit)


@app.get("/api/metrics")
def get_metrics():
    logs = fetch_logs(500)
    counts = Counter(log["level"] for log in logs)
    return {
        "total": len(logs),
        "errors": counts.get("ERROR", 0),
        "warnings": counts.get("WARNING", 0),
        "info": counts.get("INFO", 0),
    }


@app.get("/api/alerts")
def get_alerts(limit: int = Query(default=10, ge=1, le=50)):
    logs = [log for log in fetch_logs(100) if log["level"] in {"ERROR", "WARNING"}]
    return logs[:limit]


@app.get("/api/trends")
def get_trends():
    logs = fetch_logs(200)
    buckets = Counter()
    for log in logs:
        timestamp = log.get("timestamp")
        if not timestamp:
            continue
        hour = timestamp[:13] + ":00"
        if log["level"] == "ERROR":
            buckets[hour] += 1

    return [{"time": key, "errors": buckets[key]} for key in sorted(buckets.keys())[-12:]]


@app.get("/api/issues")
def get_issues():
    logs = [log for log in fetch_logs(500) if log["level"] == "ERROR"]
    counts = Counter(log["service_name"] for log in logs)
    return [
        {"service": service_name, "error_count": count}
        for service_name, count in counts.most_common(5)
    ]


@app.get("/api/notifications")
def get_notifications():
    alerts = get_alerts(5)
    return [
        {
            "message": f"{alert['level']} in {alert['service_name']}: {alert['message']}",
            "timestamp": alert["timestamp"],
        }
        for alert in alerts
    ]


@app.post("/logs", status_code=201)
def add_log_compat(log: LogIn):
    return add_log(log)


@app.get("/logs")
def get_logs_compat(limit: int = Query(default=100, ge=1, le=500)):
    return get_logs(limit)
