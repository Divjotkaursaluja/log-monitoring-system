import { useCallback, useEffect, useMemo, useState } from "react";
import { fetchLogs, fetchMetrics } from "../services/api";

const emptyMetrics = {
  total_logs: 0,
  total_errors: 0,
  total_warnings: 0,
  total_info: 0,
  active_alerts: 0,
  critical_incidents: 0,
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
  total_logs: logs.length,
  total_errors: logs.filter((log) => log.level === "ERROR").length,
  total_warnings: logs.filter((log) => log.level === "WARNING").length,
  total_info: logs.filter((log) => log.level === "INFO").length,
  total: logs.length,
  errors: logs.filter((log) => log.level === "ERROR").length,
  warnings: logs.filter((log) => log.level === "WARNING").length,
  info: logs.filter((log) => log.level === "INFO").length,
});

const normalizeMetrics = (metrics, fallbackLogs) => {
  const fallback = calculateMetrics(fallbackLogs);
  const totalLogs = metrics.total_logs ?? metrics.total ?? fallback.total_logs;
  const totalErrors = metrics.total_errors ?? metrics.errors ?? fallback.total_errors;
  const totalWarnings = metrics.total_warnings ?? metrics.warnings ?? fallback.total_warnings;
  const totalInfo = metrics.total_info ?? metrics.info ?? fallback.total_info;

  return {
    ...metrics,
    total_logs: totalLogs,
    total_errors: totalErrors,
    total_warnings: totalWarnings,
    total_info: totalInfo,
    total: totalLogs,
    errors: totalErrors,
    warnings: totalWarnings,
    info: totalInfo,
    active_alerts: metrics.active_alerts ?? 0,
    critical_incidents: metrics.critical_incidents ?? 0,
  };
};

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
        nextMetrics = normalizeMetrics(metricsResponse.data, normalizedLogs);
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
