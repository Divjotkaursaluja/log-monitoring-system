// src/components/AlertsPanel.jsx
import { useEffect, useState } from "react";
import { acknowledgeAlert, fetchAlerts, resolveAlert } from "../services/api";

const severityStyles = {
  CRITICAL: "bg-red-500/10 text-red-200 border-red-500/30",
  HIGH: "bg-orange-500/10 text-orange-200 border-orange-500/30",
  MEDIUM: "bg-yellow-500/10 text-yellow-200 border-yellow-500/30",
  LOW: "bg-slate-700/50 text-slate-200 border-slate-600",
};

const AlertsPanel = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const refresh = () => fetchAlerts().then(res => setAlerts(res.data));
    refresh();
    const interval = window.setInterval(refresh, 3000);
    return () => window.clearInterval(interval);
  }, []);

  const handleAcknowledge = async (alertId) => {
    await acknowledgeAlert(alertId);
    const response = await fetchAlerts();
    setAlerts(response.data);
  };

  const handleResolve = async (alertId) => {
    await resolveAlert(alertId);
    const response = await fetchAlerts();
    setAlerts(response.data);
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-5 shadow-xl">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-white">Active Alerts</h2>
          <p className="text-sm text-slate-400">ML-driven incidents waiting for response</p>
        </div>
        <span className="rounded-full bg-red-500/10 px-3 py-1 text-xs font-semibold text-red-200 ring-1 ring-red-500/30">
          {alerts.length} open
        </span>
      </div>

      <div className="max-h-80 space-y-3 overflow-y-auto">
        {alerts.length === 0 && (
          <div className="text-sm text-slate-400">No alerts yet.</div>
        )}
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`rounded-lg border p-3 text-sm transition ${
              severityStyles[alert.severity] || severityStyles.LOW
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{alert.severity}</span>
                <span className="text-xs text-slate-300">{alert.alert_type}</span>
                <span className="text-xs text-slate-400">{alert.category}</span>
              </div>
              <span className="text-xs text-slate-400">{alert.source_service}</span>
            </div>
            <p className="mt-2 text-slate-200">{alert.message}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {!alert.acknowledged && (
                <button
                  className="rounded-md border border-slate-600 px-3 py-1 text-xs text-slate-200 hover:bg-slate-800"
                  onClick={() => handleAcknowledge(alert.id)}
                  type="button"
                >
                  Acknowledge
                </button>
              )}
              <button
                className="rounded-md bg-cyan-500 px-3 py-1 text-xs font-semibold text-slate-950 hover:bg-cyan-400"
                onClick={() => handleResolve(alert.id)}
                type="button"
              >
                Resolve
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPanel;
