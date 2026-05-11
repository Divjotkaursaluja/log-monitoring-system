# Folder Architecture

ai-log-monitoring-frontend/
│
├── public/
│   └── index.html
│
├── src/
│   ├── assets/                # icons, images
│   ├── components/            # reusable UI components
│   │   ├── LogTable.jsx
│   │   ├── AlertsPanel.jsx
│   │   ├── TrendChart.jsx
│   │   ├── HealthStatus.jsx
│   │   ├── TopIssues.jsx
│   │   ├── Notifications.jsx
│   │   └── Navbar.jsx
│   │
│   ├── pages/
│   │   └── Dashboard.jsx
│   │
│   ├── services/              # API calls
│   │   └── api.js
│   │
│   ├── hooks/                # custom hooks (polling / websocket)
│   │   └── useLogs.js
│   │
│   ├── utils/
│   │   └── constants.js
│   │
│   ├── App.jsx
│   ├── main.jsx
│   └── styles.css
│
├── package.json
└── README.md



# 🚀 AI Powered Log Monitoring System – Backend API Documentation

## 📌 Overview

This document defines all required backend APIs for the **AI Powered Log Monitoring Dashboard**.

The goal is to build a system where:

* Logs are collected and processed
* AI classifies logs
* Alerts are generated
* Frontend dashboard updates in **real-time**

---

## 🎯 System Goal

> “The dashboard is not just for viewing logs, it transforms raw data into actionable insights, helping developers detect, understand, and prevent system failures efficiently.”

---

## ⚙️ Base URL

```
http://localhost:5000
```

---

# 📡 API ENDPOINTS

---

## 🟢 1. Get Logs (Real-Time Feed)

### Endpoint

```
GET /api/logs
```

### Response

```json
[
  {
    "id": 1,
    "timestamp": "2026-01-10T12:30:45",
    "service": "auth-service",
    "message": "User login failed",
    "level": "error"
  }
]
```

### Notes

* Used for initial log loading
* Real-time updates handled via WebSocket

---

## 🚨 2. Alerts API

### Endpoint

```
GET /api/alerts
```

### Response

```json
[
  {
    "id": 1,
    "message": "High error rate detected",
    "severity": "high",
    "time": "2026-01-10T12:31:00"
  }
]
```

### Severity Values

```
high | warning
```

---

## 📈 3. Error Trends API

### Endpoint

```
GET /api/trends
```

### Response

```json
[
  {
    "time": "12:00",
    "errors": 5
  },
  {
    "time": "12:05",
    "errors": 12
  }
]
```

### Notes

* Used for graph plotting
* Helps detect spikes and patterns

---

## ⚡ 4. System Health API

### Endpoint

```
GET /api/health
```

### Response

```json
{
  "status": "healthy"
}
```

### Status Values

```
healthy | warning | critical
```

---

## 🔥 5. Top Issues API

### Endpoint

```
GET /api/issues
```

### Response

```json
[
  {
    "service": "payment-service",
    "error_count": 45
  }
]
```

---

## 🔔 6. Notifications API

### Endpoint

```
GET /api/notifications
```

### Response

```json
[
  {
    "message": "Alert email sent to dev team",
    "time": "2026-01-10T12:32:00"
  }
]
```

---

## 🧠 7. AI Classification API

### Endpoint

```
GET /api/classification
```

### Response

```json
[
  {
    "type": "Login Issues",
    "count": 30
  },
  {
    "type": "Payment Errors",
    "count": 12
  }
]
```

---

# 🔁 REAL-TIME LOG STREAM (WebSocket)

---

## 🔌 WebSocket Endpoint

```
ws://localhost:5000/ws/logs
```

---

## 📥 Data Format (Server → Client)

```json
{
  "id": 101,
  "timestamp": "2026-01-10T12:35:00",
  "service": "payment-service",
  "message": "Transaction failed",
  "level": "error"
}
```

---

## ⚡ Behavior

* Client connects once
* Server pushes new logs automatically
* No polling required

---

# 🧠 SYSTEM FLOW

```
User action
   ↓
Log generated
   ↓
FastAPI stores logs
   ↓
AI classifies logs
   ↓
Alerts generated
   ↓
WebSocket pushes updates
   ↓
Frontend updates instantly ⚡
```

---

# 🔐 CORS CONFIGURATION (REQUIRED)

Add this in FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

# 🧩 OPTIONAL BACKEND ENHANCEMENTS

* Log storage using PostgreSQL / MongoDB
* Kafka / Redis for streaming logs
* AI model for classification
* Rate limiting alerts
* Email/SMS notification service

---

# ⚠️ IMPORTANT NOTES

* All timestamps must be ISO format
* APIs must return JSON only
* WebSocket should send data in real-time
* Maintain consistent field naming

---

# 💥 FINAL STATEMENT

> “This system converts raw logs into meaningful insights, enabling developers to monitor, analyze, and prevent failures in real time.”

---

## ✅ Backend Ready Checklist

* [ ] All APIs implemented
* [ ] WebSocket working
* [ ] CORS enabled
* [ ] Proper JSON format
* [ ] Real-time log push working

---
