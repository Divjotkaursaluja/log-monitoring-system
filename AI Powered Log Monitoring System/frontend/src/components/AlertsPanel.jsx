// src/components/AlertsPanel.jsx
import { useEffect, useState } from "react";
import { fetchAlerts } from "../services/api";

const AlertsPanel = () => {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchAlerts().then(res => setAlerts(res.data));
  }, []);

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl">
      <h2 className="text-sm text-gray-400 mb-4">Alerts</h2>

      <div className="space-y-3 max-h-40 overflow-y-auto">
        {/* realtime data */}
        {alerts.map((alert, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg text-sm transition ${alert.severity === "high"
                ? "bg-red-500/10 text-red-300 border border-red-500/20"
                : "bg-yellow-500/10 text-yellow-300 border border-yellow-500/20"
              }`}
          >
            {alert.message}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlertsPanel;