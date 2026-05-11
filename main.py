from fastapi import FastAPI
from pydantic import BaseModel
from db import get_connection
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class Log(BaseModel):
    level: str
    message: str
    service_name: str

@app.post("/logs")
def add_log(log: Log):
    conn = get_connection()
    cursor = conn.cursor()

    query = "INSERT INTO logs (level, message, service_name) VALUES (%s, %s, %s)"
    cursor.execute(query, (log.level, log.message, log.service_name))

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Log stored successfully"}

@app.get("/api/logs")
def get_logs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return logs
@app.get("/api/metrics")
def get_metrics():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) as total FROM logs")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as errors FROM logs WHERE level='ERROR'")
    errors = cursor.fetchone()["errors"]

    cursor.execute("SELECT COUNT(*) as info FROM logs WHERE level='INFO'")
    info = cursor.fetchone()["info"]

    cursor.close()
    conn.close()

    return {
        "total_logs": total,
        "error_logs": errors,
        "info_logs": info
    }