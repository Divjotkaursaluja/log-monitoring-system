import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000"
});

// Logs
export const fetchLogs = () => API.get("/api/logs");

// Metrics
export const fetchMetrics = () => API.get("/api/metrics");

// Alerts
export const fetchAlerts = () => API.get("/api/alerts");

// Health
export const fetchHealth = () => API.get("/api/health");

// Notifications
export const fetchNotifications = () => API.get("/api/notifications");

// Issues
export const fetchIssues = () => API.get("/api/issues");

// Trends
export const fetchTrends = () => API.get("/api/trends");