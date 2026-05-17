import { useEffect, useState } from "react";
import { fetchAlertHistory } from "../services/api";

const badgeStyles = {
  CRITICAL: "bg-red-500/10 text-red-200 ring-red-500/30",
  HIGH: "bg-orange-500/10 text-orange-200 ring-orange-500/30",
  MEDIUM: "bg-yellow-500/10 text-yellow-200 ring-yellow-500/30",
  LOW: "bg-slate-700/60 text-slate-200 ring-slate-600",
};

const formatTimestamp = (value) => {
  if (!value) return "Pending";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const AlertHistory = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const refresh = () => fetchAlertHistory().then((res) => setAlerts(res.data));
    refresh();
    const interval = window.setInterval(refresh, 3000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-950/70 shadow-xl">
      <div className="border-b border-slate-800 px-5 py-4">
        <h2 className="text-lg font-semibold text-white">Alert History</h2>
        <p className="text-sm text-slate-400">Incident records persisted in MySQL</p>
      </div>

      <div className="max-h-[360px] overflow-auto">
        <table className="w-full min-w-[860px] text-left text-sm">
          <thead className="sticky top-0 bg-slate-900 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-3 font-semibold">Created</th>
              <th className="px-5 py-3 font-semibold">Severity</th>
              <th className="px-5 py-3 font-semibold">Category</th>
              <th className="px-5 py-3 font-semibold">Service</th>
              <th className="px-5 py-3 font-semibold">Status</th>
              <th className="px-5 py-3 font-semibold">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {alerts.length === 0 && (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan="6">
                  No alert history yet.
                </td>
              </tr>
            )}
            {alerts.map((alert) => (
              <tr key={alert.id} className="hover:bg-slate-900/70">
                <td className="whitespace-nowrap px-5 py-4 text-slate-300">
                  {formatTimestamp(alert.created_at)}
                </td>
                <td className="px-5 py-4">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                      badgeStyles[alert.severity] || badgeStyles.LOW
                    }`}
                  >
                    {alert.severity}
                  </span>
                </td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-300">{alert.category}</td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-300">{alert.source_service}</td>
                <td className="whitespace-nowrap px-5 py-4 text-slate-300">{alert.status}</td>
                <td className="px-5 py-4 text-slate-300">{alert.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default AlertHistory;
