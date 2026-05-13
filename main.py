from datetime import datetime, timezone
from hashlib import sha256
from socket import gethostname
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import get_connection


app = FastAPI(title="AI Powered Log Monitoring System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KNOWN_LEVELS = {"ERROR", "WARNING", "INFO"}


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

    ensure_column(cursor, "logs", "agent_id", "agent_id VARCHAR(64) NULL")
    ensure_column(cursor, "logs", "source_file", "source_file VARCHAR(500) NULL")
    ensure_column(cursor, "logs", "received_at", "received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    conn.commit()
    cursor.close()
    conn.close()


@app.on_event("startup")
def startup():
    init_schema()


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
    cursor = conn.cursor()
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
    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Log stored successfully", "level": level}


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
        SELECT id, level, message, service_name, timestamp, agent_id, source_file
        FROM logs
        ORDER BY id DESC
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
        SELECT level, message
        FROM logs
        WHERE level IN ('ERROR', 'WARNING')
        ORDER BY id DESC
        LIMIT 10
        """
    )
    alerts = [
        {"severity": "high" if row["level"] == "ERROR" else "medium", "message": row["message"]}
        for row in cursor.fetchall()
    ]
    cursor.close()
    conn.close()
    return alerts


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
    cursor.execute("SELECT message FROM logs ORDER BY id DESC LIMIT 5")
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
