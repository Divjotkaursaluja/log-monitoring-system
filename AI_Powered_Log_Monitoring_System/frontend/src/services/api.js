import axios from "axios";

const API = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

API.interceptors.response.use((response) => {
  console.log(`[API] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data);
  return response;
});

export const signup = (payload) => API.post("/auth/signup", payload);
export const login = (payload) => API.post("/auth/login", payload);
export const fetchMe = () => API.get("/auth/me");

// Logs
export const fetchLogs = () => API.get("/api/logs");

// Metrics
export const fetchMetrics = () => API.get("/api/metrics");

// Alerts
export const fetchAlerts = () => API.get("/api/alerts");
export const fetchAlertHistory = () => API.get("/api/alerts/history");
export const acknowledgeAlert = (alertId) => API.post(`/api/alerts/${alertId}/acknowledge`);
export const resolveAlert = (alertId) => API.post(`/api/alerts/${alertId}/resolve`);

// Health
export const fetchHealth = () => API.get("/api/health");

// Notifications
export const fetchNotifications = () => API.get("/api/notifications");

// Issues
export const fetchIssues = () => API.get("/api/issues");

// Trends
export const fetchTrends = () => API.get("/api/trends");
