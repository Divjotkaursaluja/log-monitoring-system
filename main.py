from fastapi import FastAPI
from pydantic import BaseModel
from db import get_connection

app = FastAPI()

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

@app.get("/logs")
def get_logs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM logs")
    logs = cursor.fetchall()

    cursor.close()
    conn.close()

    return logs