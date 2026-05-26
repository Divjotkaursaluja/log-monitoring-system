import json
import os
import platform
import queue
import socket
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import psutil
import requests
import yaml


AGENT_VERSION = "1.0.0"
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
BUNDLED_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR))
STATE_FILE = APP_DIR / "agent_state.json"
QUEUE_FILE = APP_DIR / "buffered_logs.jsonl"


def load_config():
    config_path = APP_DIR / "config.yaml"
    if not config_path.exists():
        config_path = BUNDLED_DIR / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


CONFIG = load_config()
BACKEND_URL = CONFIG["backend_url"].rstrip("/")
SERVICE_NAME = CONFIG["service_name"]
ORGANIZATION_KEY = CONFIG.get("organization_key")
LOG_FILES = CONFIG["log_files"]
FROM_START = bool(CONFIG.get("from_start", False))
HEARTBEAT_INTERVAL = int(CONFIG.get("heartbeat_interval_seconds", 30))
RETRY_INTERVAL = int(CONFIG.get("retry_interval_seconds", 5))
REQUEST_TIMEOUT = int(CONFIG.get("request_timeout_seconds", 5))

send_queue: queue.Queue[dict] = queue.Queue()
stop_event = threading.Event()


def classify_log(line: str) -> str:
    upper = line.upper()
    if any(token in upper for token in ("ERROR", "FAILED", "EXCEPTION", "CRITICAL", "TRACEBACK")):
        return "ERROR"
    if any(token in upper for token in ("WARNING", "WARN", "TIMEOUT", "RETRY", "DUPLICATE")):
        return "WARNING"
    return "INFO"


def load_state():
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, indent=2)


def clear_state(reason):
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    print(f"Cleared agent registration state: {reason}")


def auth_headers():
    state = load_state()
    token = state.get("token")
    if not token:
        raise RuntimeError("Agent is not registered and has no token.")
    return {"Authorization": f"Bearer {token}"}


def register_agent():
    state = load_state()
    if state.get("agent_id") and state.get("token"):
        print(f"Agent already registered: {state['agent_id']}")
        return state

    payload = {
        "machine_name": socket.gethostname(),
        "service_name": SERVICE_NAME,
        "agent_version": AGENT_VERSION,
    }
    if ORGANIZATION_KEY:
        payload["organization_key"] = ORGANIZATION_KEY
    response = requests.post(
        f"{BACKEND_URL}/register-agent",
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    state = response.json()
    state["registered_at"] = datetime.utcnow().isoformat()
    state["platform"] = platform.platform()
    save_state(state)
    print(f"Registered agent: {state['agent_id']}")
    return state


def append_to_disk_queue(payload):
    with open(QUEUE_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(payload) + "\n")


def load_disk_queue():
    if not QUEUE_FILE.exists():
        return

    pending = []
    with open(QUEUE_FILE, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            try:
                pending.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    QUEUE_FILE.unlink(missing_ok=True)
    for payload in pending:
        send_queue.put(payload)
    print(f"Loaded {len(pending)} buffered logs from disk.")


def send_payload(payload):
    response = requests.post(
        f"{BACKEND_URL}/logs",
        json=payload,
        headers=auth_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code == 401:
        clear_state("backend rejected saved token while sending logs")
        register_agent()
        response = requests.post(
            f"{BACKEND_URL}/logs",
            json=payload,
            headers=auth_headers(),
            timeout=REQUEST_TIMEOUT,
        )
    response.raise_for_status()
    print("backend response:", response.json())


def retry_worker():
    while not stop_event.is_set():
        payload = send_queue.get()
        try:
            send_payload(payload)
            print(f"sent {payload['level']} from {payload.get('source_file')}")
        except requests.RequestException as exc:
            print(f"send failed; buffering locally: {exc}")
            append_to_disk_queue(payload)
            time.sleep(RETRY_INTERVAL)
        finally:
            send_queue.task_done()


def build_log_payload(line, source_file):

    clean_line = (
        line.encode("utf-8", errors="ignore")
            .decode("utf-8", errors="ignore")
            .replace("\x00", "")
            .replace("�", "")
            .strip()
    )

    payload = {
        "level": classify_log(clean_line),
        "message": clean_line,
        "service_name": SERVICE_NAME,
        "source_file": source_file,
    }

    print("detected log:", payload)

    return payload


def follow_file(path):
    log_path = Path(path)

    while not log_path.exists():
        print(f"Waiting for log file: {log_path}")
        time.sleep(2)

    print(f"Watching {log_path}")

    with open(log_path, "r", encoding="utf-8", errors="replace") as file:
    

        # move to end only if from_start false
        if not FROM_START:
            file.seek(0, os.SEEK_END)

        while not stop_event.is_set():

            line = file.readline()

            if not line:
                time.sleep(0.5)
                continue

            line = line.strip()

            if line:
                payload = build_log_payload(line, str(log_path))
                send_queue.put(payload)


def heartbeat_worker():
    while not stop_event.is_set():
        payload = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage(str(Path.home().anchor or "C:\\")).percent,
        }
        try:
            response = requests.post(
                f"{BACKEND_URL}/agent/heartbeat",
                json=payload,
                headers=auth_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 401:
                clear_state("backend rejected saved token while sending heartbeat")
                register_agent()
                response = requests.post(
                    f"{BACKEND_URL}/agent/heartbeat",
                    json=payload,
                    headers=auth_headers(),
                    timeout=REQUEST_TIMEOUT,
                )
            response.raise_for_status()
            print("heartbeat sent")
        except requests.RequestException as exc:
            print(f"heartbeat failed: {exc}")

        stop_event.wait(HEARTBEAT_INTERVAL)


def start_agent():
    register_agent()
    load_disk_queue()

    threading.Thread(target=retry_worker, daemon=True).start()
    threading.Thread(target=heartbeat_worker, daemon=True).start()

    for log_file in LOG_FILES:
        threading.Thread(target=follow_file, args=(log_file,), daemon=True).start()

    print("Monitoring Agent Started.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_event.set()
        print("Monitoring Agent stopped.")


if __name__ == "__main__":
    start_agent()
