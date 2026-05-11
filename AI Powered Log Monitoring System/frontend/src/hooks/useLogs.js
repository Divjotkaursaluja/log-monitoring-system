import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchLogs, fetchMetrics } from "../services/api";

const emptyMetrics = {
  total: 0,
  errors: 0,
  warnings: 0,
  info: 0,
};

const normalizeLog = (log) => ({
  ...log,
  level: String(log.level || "INFO").toUpperCase(),
  service_name: log.service_name || log.service || "unknown-service",
});

const calculateMetrics = (logs) => ({
  total: logs.length,
  errors: logs.filter((log) => log.level === "ERROR").length,
  warnings: logs.filter((log) => log.level === "WARNING").length,
  info: logs.filter((log) => log.level === "INFO").length,
});

const useLogs = (refreshMs = 3000) => {
  const [logs, setLogs] = useState([]);
  const [metrics, setMetrics] = useState(emptyMetrics);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const logsResponse = await fetchLogs(100);
      const normalizedLogs = logsResponse.data.map(normalizeLog);
      let nextMetrics = calculateMetrics(normalizedLogs);

      try {
        const metricsResponse = await fetchMetrics();
        nextMetrics = metricsResponse.data;
      } catch {
        nextMetrics = calculateMetrics(normalizedLogs);
      }

      setLogs(normalizedLogs);
      setMetrics(nextMetrics);
      setError("");
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || "Unable to load logs");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, refreshMs);
    return () => window.clearInterval(interval);
  }, [refresh, refreshMs]);

  return useMemo(
    () => ({ logs, metrics, loading, error, lastUpdated, refresh }),
    [logs, metrics, loading, error, lastUpdated, refresh],
  );
};

export default useLogs;
