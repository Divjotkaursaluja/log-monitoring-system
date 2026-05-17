from datetime import datetime, timezone
from hashlib import sha256
from socket import gethostname
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from alerts.engine import evaluate_alert, save_alert
from ai_engine.schemas import LogContext, NormalizedLog
from ai_engine.service import AIAnalysisService
from db import get_connection
from notification.service import notify_developers


app = FastAPI(title="AI Powered Log Monitoring System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KNOWN_LEVELS = {"ERROR", "WARNING", "INFO"}
ai_service: AIAnalysisService | None = None


class AgentRegistrationRequest(BaseModel):
    machine_name: str = Field(default_factory=gethostname)
    service_name: str = Field(..., min_length=1)
    agent_version: str = "1.0.0"


class LogIn(BaseModel):
    level: str | None = None
    message: str = Field(..., min_length=1)
    service_name: str | None = None
    source_file: str | None = None
    timestamp: datetime | None = None


class HeartbeatIn(BaseModel):
    cpu_percent: float = Field(ge=0)
    ram_percent: float = Field(ge=0)
    disk_percent: float = Field(ge=0)


class AIAnalyzeRequest(BaseModel):
    level: str = "INFO"
    message: str = Field(..., min_length=1)
    service_name: str = Field(..., min_length=1)
    timestamp: datetime | None = None


class AlertStatusUpdate(BaseModel):
    acknowledged: bool | None = None
    resolved: bool | None = None
    status: str | None = None


def token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def classify_severity(message: str, level: str | None = None) -> str:
    normalized = (level or "").strip().upper()
    if normalized in KNOWN_LEVELS:
        return normalized

    upper_message = message.upper()
    if any(word in upper_message for word in ("ERROR", "FAILED", "EXCEPTION", "CRITICAL", "TRACEBACK")):
        return "ERROR"
    if any(word in upper_message for word in ("WARNING", "WARN", "TIMEOUT", "RETRY", "DUPLICATE")):
        return "WARNING"
    return "INFO"


def ensure_column(cursor, table_name: str, column_name: str, ddl: str):
    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        (table_name, column_name),
    )
    if cursor.fetchone()["total"] == 0:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")


def init_schema():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            level VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            service_name VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agents (
            agent_id VARCHAR(64) PRIMARY KEY,
            machine_name VARCHAR(255) NOT NULL,
            token VARCHAR(128) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            service_name VARCHAR(255) NOT NULL,
            agent_version VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_heartbeats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            agent_id VARCHAR(64) NOT NULL,
            cpu_percent DECIMAL(5,2) NOT NULL,
            ram_percent DECIMAL(5,2) NOT NULL,
            disk_percent DECIMAL(5,2) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'ONLINE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_heartbeats_agent_created (agent_id, created_at),
            CONSTRAINT fk_heartbeats_agent
                FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_log_analysis (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_id INT NOT NULL,
            predicted_category VARCHAR(100) NOT NULL,
            predicted_severity VARCHAR(50) NOT NULL,
            is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
            anomaly_score FLOAT NULL,
            confidence FLOAT NULL,
            insight TEXT,
            model_version VARCHAR(50) DEFAULT 'baseline-v1',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_ai_log_id (log_id),
            INDEX idx_ai_category (predicted_category),
            INDEX idx_ai_anomaly (is_anomaly),
            CONSTRAINT fk_ai_log_analysis_log
                FOREIGN KEY (log_id) REFERENCES logs(id)
                ON DELETE CASCADE
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            log_id INT NOT NULL,
            alert_type VARCHAR(100) NOT NULL,
            severity VARCHAR(50) NOT NULL,
            category VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(30) NOT NULL DEFAULT 'OPEN',
            acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
            resolved BOOLEAN NOT NULL DEFAULT FALSE,
            source_service VARCHAR(255) NOT NULL,
            INDEX idx_alerts_log_id (log_id),
            INDEX idx_alerts_status_created (status, created_at),
            INDEX idx_alerts_severity (severity),
            CONSTRAINT fk_alerts_log
                FOREIGN KEY (log_id) REFERENCES logs(id)
                ON DELETE CASCADE
        )
        """
    )

    ensure_column(cursor, "logs", "agent_id", "agent_id VARCHAR(64) NULL")
    ensure_column(cursor, "logs", "source_file", "source_file VARCHAR(500) NULL")
    ensure_column(cursor, "logs", "received_at", "received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    cursor.close()
    conn.close()


@app.on_event("startup")
def startup():
    init_schema()


def get_ai_service() -> AIAnalysisService:
    global ai_service
    if ai_service is None:
        ai_service = AIAnalysisService()
    return ai_service


def get_recent_log_context(cursor, service_name: str) -> LogContext:
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
    error_count = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM logs
        WHERE service_name=%s
          AND level='WARNING'
          AND timestamp >= (CURRENT_TIMESTAMP - INTERVAL 5 MINUTE)
        """,
        (service_name,),
    )
    warning_count = cursor.fetchone()["total"]

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM logs
        WHERE service_name=%s
          AND timestamp >= (CURRENT_TIMESTAMP - INTERVAL 5 MINUTE)
        """,
        (service_name,),
    )
    service_log_count = cursor.fetchone()["total"]

    return LogContext(
        error_count=error_count,
        warning_count=warning_count,
        service_log_count=service_log_count,
    )


def save_ai_analysis(cursor, log_id: int, analysis):
    cursor.execute(
        """
        INSERT INTO ai_log_analysis (
            log_id,
            predicted_category,
            predicted_severity,
            is_anomaly,
            anomaly_score,
            confidence,
            insight,
            model_version
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            log_id,
            analysis.predicted_category,
            analysis.predicted_severity,
            analysis.is_anomaly,
            analysis.anomaly_score,
            analysis.confidence,
            analysis.insight,
            analysis.model_version,
        ),
    )


def trigger_alert_if_needed(cursor, log_id: int, level: str, log: LogIn, service_name: str, analysis):
    if not hasattr(analysis, "predicted_category"):
        return None

    decision = evaluate_alert(cursor, log_id, level, log.message, service_name, analysis)
    if not decision.should_alert:
        return None

    alert_id = save_alert(cursor, log_id, service_name, decision)
    alert_payload = {
        "id": alert_id,
        "log_id": log_id,
        "alert_type": decision.alert_type,
        "severity": decision.severity,
        "category": decision.category,
        "message": decision.message,
        "source_service": service_name,
        "reasons": decision.reasons,
    }
    notify_developers(alert_payload, decision.notify_email)
    return alert_payload


def print_ai_debug(log: LogIn, level: str, service_name: str, analysis):
    if not hasattr(analysis, "predicted_category"):
        print("AI analysis failed:", analysis)
        return

    print("Incoming log:")
    print(log.message)
    print("Prediction:")
    print(f"category = {analysis.predicted_category}")
    print(f"severity = {analysis.predicted_severity}")
    print(f"anomaly = {analysis.is_anomaly}")
    print(f"confidence = {analysis.confidence}")
    print(f"anomaly_score = {analysis.anomaly_score}")
    print(f"service = {service_name}")
    print(f"stored_table = ai_log_analysis")


def get_authorized_agent(authorization: Annotated[str | None, Header()] = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing agent token")

    raw_token = authorization.removeprefix("Bearer ").strip()
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT agent_id, machine_name, service_name, status
        FROM agents
        WHERE token = %s
        """,
        (token_hash(raw_token),),
    )
    agent = cursor.fetchone()

    if not agent:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown agent token")

    cursor.execute(
        "UPDATE agents SET status='ONLINE', last_seen=CURRENT_TIMESTAMP WHERE agent_id=%s",
        (agent["agent_id"],),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return agent


@app.post("/register-agent")
def register_agent(payload: AgentRegistrationRequest):
    agent_id = str(uuid4())
    token = str(uuid4())

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO agents (agent_id, machine_name, token, status, service_name, agent_version)
        VALUES (%s, %s, %s, 'ONLINE', %s, %s)
        """,
        (agent_id, payload.machine_name, token_hash(token), payload.service_name, payload.agent_version),
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {
        "agent_id": agent_id,
        "token": token,
        "machine_name": payload.machine_name,
        "service_name": payload.service_name,
    }


@app.post("/logs", status_code=201)
def add_log(log: LogIn, agent=Depends(get_authorized_agent)):
    level = classify_severity(log.message, log.level)
    service_name = log.service_name or agent["service_name"]

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if log.timestamp:
        cursor.execute(
            """
            INSERT INTO logs (level, message, service_name, timestamp, agent_id, source_file)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (level, log.message, service_name, log.timestamp, agent["agent_id"], log.source_file),
        )
    else:
        cursor.execute(
            """
            INSERT INTO logs (level, message, service_name, agent_id, source_file)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (level, log.message, service_name, agent["agent_id"], log.source_file),
        )
    log_id = cursor.lastrowid

    ai_analysis = None
    alert_payload = None
    try:
        context = get_recent_log_context(cursor, service_name)
        ai_analysis = get_ai_service().analyze_log(
            NormalizedLog(
                level=level,
                message=log.message,
                service_name=service_name,
                timestamp=log.timestamp,
            ),
            context,
        )
        print_ai_debug(log, level, service_name, ai_analysis)
        save_ai_analysis(cursor, log_id, ai_analysis)
        alert_payload = trigger_alert_if_needed(cursor, log_id, level, log, service_name, ai_analysis)
    except Exception as exc:
        ai_analysis = {"error": f"AI analysis skipped: {exc}"}
        print("AI analysis skipped:", exc)

    conn.commit()
    cursor.close()
    conn.close()

    if hasattr(ai_analysis, "model_dump"):
        ai_payload = ai_analysis.model_dump()
    elif hasattr(ai_analysis, "dict"):
        ai_payload = ai_analysis.dict()
    else:
        ai_payload = ai_analysis

    return {
        "message": "Log stored successfully",
        "level": level,
        "log_id": log_id,
        "ai_analysis": ai_payload,
        "alert": alert_payload,
    }


@app.post("/agent/heartbeat")
def add_heartbeat(heartbeat: HeartbeatIn, agent=Depends(get_authorized_agent)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO agent_heartbeats (agent_id, cpu_percent, ram_percent, disk_percent, status)
        VALUES (%s, %s, %s, %s, 'ONLINE')
        """,
        (agent["agent_id"], heartbeat.cpu_percent, heartbeat.ram_percent, heartbeat.disk_percent),
    )
    cursor.execute(
        "UPDATE agents SET status='ONLINE', last_seen=CURRENT_TIMESTAMP WHERE agent_id=%s",
        (agent["agent_id"],),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Heartbeat stored"}


@app.get("/api/logs")
def get_logs(limit: int = Query(default=100, ge=1, le=1000)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            l.id,
            l.level,
            l.message,
            l.service_name,
            l.timestamp,
            l.agent_id,
            l.source_file,
            a.predicted_category,
            a.predicted_severity,
            a.is_anomaly,
            a.anomaly_score,
            a.confidence,
            a.insight,
            a.model_version
        FROM logs l
        LEFT JOIN ai_log_analysis a ON a.log_id = l.id
        ORDER BY l.id DESC
        LIMIT %s
        """,
        (limit,),
    )
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs


@app.get("/api/metrics")
def get_metrics():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM logs")
    total_logs = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM logs WHERE level='ERROR'")
    total_errors = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM logs WHERE level='WARNING'")
    total_warnings = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM logs WHERE level='INFO'")
    total_info = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM agents WHERE status='ONLINE'")
    online_agents = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM alerts WHERE resolved = FALSE")
    active_alerts = cursor.fetchone()["total"]
    cursor.execute("SELECT COUNT(*) AS total FROM alerts WHERE severity='CRITICAL' AND resolved = FALSE")
    critical_incidents = cursor.fetchone()["total"]
    cursor.close()
    conn.close()

    return {
        "total_logs": total_logs,
        "total_errors": total_errors,
        "total_warnings": total_warnings,
        "total_info": total_info,
        "total": total_logs,
        "errors": total_errors,
        "warnings": total_warnings,
        "info": total_info,
        "online_agents": online_agents,
        "active_alerts": active_alerts,
        "critical_incidents": critical_incidents,
    }


@app.get("/api/agents")
def get_agents():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT agent_id, machine_name, service_name, status, last_seen, agent_version, created_at
        FROM agents
        ORDER BY last_seen DESC
        """
    )
    agents = cursor.fetchall()
    cursor.close()
    conn.close()
    return agents


@app.get("/api/alerts")
def get_alerts():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            log_id,
            alert_type,
            severity,
            category,
            message,
            created_at,
            status,
            acknowledged,
            resolved,
            source_service
        FROM alerts
        WHERE resolved = FALSE
        ORDER BY created_at DESC
        LIMIT 10
        """
    )
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return alerts


@app.get("/api/alerts/history")
def get_alert_history(limit: int = Query(default=100, ge=1, le=500)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            id,
            log_id,
            alert_type,
            severity,
            category,
            message,
            created_at,
            status,
            acknowledged,
            resolved,
            source_service
        FROM alerts
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return alerts


@app.patch("/api/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertStatusUpdate):
    updates = []
    values = []
    if payload.acknowledged is not None:
        updates.append("acknowledged=%s")
        values.append(payload.acknowledged)
    if payload.resolved is not None:
        updates.append("resolved=%s")
        values.append(payload.resolved)
    if payload.status is not None:
        updates.append("status=%s")
        values.append(payload.status)

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No alert fields supplied")

    values.append(alert_id)
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"UPDATE alerts SET {', '.join(updates)} WHERE id=%s", tuple(values))
    if cursor.rowcount == 0:
        conn.rollback()
        cursor.close()
        conn.close()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    conn.commit()
    cursor.execute(
        """
        SELECT id, log_id, alert_type, severity, category, message, created_at, status,
               acknowledged, resolved, source_service
        FROM alerts
        WHERE id=%s
        """,
        (alert_id,),
    )
    alert = cursor.fetchone()
    cursor.close()
    conn.close()
    return alert


@app.post("/api/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int):
    return update_alert(alert_id, AlertStatusUpdate(acknowledged=True, status="ACKNOWLEDGED"))


@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int):
    return update_alert(alert_id, AlertStatusUpdate(acknowledged=True, resolved=True, status="RESOLVED"))


@app.post("/api/ai/analyze-log")
def analyze_log_preview(payload: AIAnalyzeRequest):
    level = classify_severity(payload.message, payload.level)
    analysis = get_ai_service().analyze_log(
        NormalizedLog(
            level=level,
            message=payload.message,
            service_name=payload.service_name,
            timestamp=payload.timestamp,
        )
    )
    return analysis


@app.get("/api/ai/insights")
def get_ai_insights(limit: int = Query(default=50, ge=1, le=500)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            l.id AS log_id,
            l.level,
            l.message,
            l.service_name,
            l.timestamp,
            a.predicted_category,
            a.predicted_severity,
            a.is_anomaly,
            a.anomaly_score,
            a.confidence,
            a.insight,
            a.model_version,
            a.created_at
        FROM ai_log_analysis a
        JOIN logs l ON l.id = a.log_id
        ORDER BY a.id DESC
        LIMIT %s
        """,
        (limit,),
    )
    insights = cursor.fetchall()
    cursor.close()
    conn.close()
    return insights


@app.get("/api/ai/logs/{log_id}/analysis")
def get_log_ai_analysis(log_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            l.id AS log_id,
            l.level,
            l.message,
            l.service_name,
            l.timestamp,
            a.predicted_category,
            a.predicted_severity,
            a.is_anomaly,
            a.anomaly_score,
            a.confidence,
            a.insight,
            a.model_version,
            a.created_at
        FROM ai_log_analysis a
        JOIN logs l ON l.id = a.log_id
        WHERE l.id = %s
        ORDER BY a.id DESC
        LIMIT 1
        """,
        (log_id,),
    )
    analysis = cursor.fetchone()
    cursor.close()
    conn.close()

    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI analysis not found")

    return analysis


@app.get("/api/ai/anomalies")
def get_ai_anomalies(limit: int = Query(default=50, ge=1, le=500)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            l.id AS log_id,
            l.level,
            l.message,
            l.service_name,
            l.timestamp,
            a.predicted_category,
            a.predicted_severity,
            a.anomaly_score,
            a.insight,
            a.created_at
        FROM ai_log_analysis a
        JOIN logs l ON l.id = a.log_id
        WHERE a.is_anomaly = TRUE
        ORDER BY a.id DESC
        LIMIT %s
        """,
        (limit,),
    )
    anomalies = cursor.fetchall()
    cursor.close()
    conn.close()
    return anomalies


@app.get("/api/ai/service-health")
def get_ai_service_health():
    service = get_ai_service()
    return {
        "status": "ready",
        "model_version": service.model_version,
        "classifier": service.classifier.__class__.__name__,
        "anomaly_detector": service.anomaly_detector.__class__.__name__,
    }


@app.get("/api/health")
def get_health():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM logs WHERE level='ERROR'")
    errors = cursor.fetchone()["total"]
    cursor.close()
    conn.close()

    if errors > 50:
        status_value = "critical"
    elif errors > 20:
        status_value = "warning"
    else:
        status_value = "healthy"
    return {"status": status_value, "checked_at": datetime.now(timezone.utc).isoformat()}


@app.get("/api/issues")
def get_issues():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT service_name, COUNT(*) AS error_count
        FROM logs
        WHERE level='ERROR'
        GROUP BY service_name
        ORDER BY error_count DESC
        LIMIT 5
        """
    )
    issues = [{"service": row["service_name"], "error_count": row["error_count"]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return issues


@app.get("/api/notifications")
def get_notifications():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT message, severity, category, created_at
        FROM alerts
        WHERE resolved = FALSE
        ORDER BY created_at DESC
        LIMIT 5
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


@app.get("/api/trends")
def get_trends():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT DATE(timestamp) AS day, COUNT(*) AS errors
        FROM logs
        WHERE level='ERROR'
        GROUP BY DATE(timestamp)
        ORDER BY day
        """
    )
    trends = [{"time": str(row["day"]), "errors": row["errors"]} for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return trends
