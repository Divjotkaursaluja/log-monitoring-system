import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000"
});

// Logs
export const fetchLogs = () => API.get("/api/logs");

// Metrics
export const fetchMetrics = () => API.get("/api/metrics");