// src/components/HealthStatus.jsx
import { useEffect, useState } from "react";
import { fetchHealth } from "../services/api";

const HealthStatus = () => {
  const [status, setStatus] = useState("");

  useEffect(() => {
    fetchHealth().then(res => setStatus(res.data.status));
  }, []);

  const color = {
    healthy: "text-green-400",
    warning: "text-yellow-400",
    critical: "text-red-400",
  };

  return (
    <div className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl">
      <h2 className="text-sm text-gray-400 mb-2">System Health</h2>

      <div className={`text-3xl font-bold ${color[status]} flex items-center gap-2`}>
        ● {status.toUpperCase()}
      </div>
    </div>
  );
};

export default HealthStatus;