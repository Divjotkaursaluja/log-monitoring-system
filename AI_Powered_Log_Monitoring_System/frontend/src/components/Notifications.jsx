// src/components/Notifications.jsx
import { useEffect, useState } from "react";
import { fetchNotifications } from "../services/api";

const Notifications = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const refresh = () => fetchNotifications().then(res => setData(res.data));
    refresh();
    const interval = window.setInterval(refresh, 3000);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10 shadow-lg">
      <h2 className="text-lg mb-4">Notifications</h2>

      {/* realtime data */}
      {data.length === 0 && (
        <div className="text-sm text-slate-400">No notifications yet.</div>
      )}
      {data.map((n, i) => (
        <div key={i} className="text-sm py-2 border-b border-slate-700">
          <div className="flex items-center justify-between gap-3">
            <span>{n.message}</span>
            {n.severity && (
              <span className="rounded-full bg-red-500/10 px-2 py-1 text-xs text-red-200">
                {n.severity}
              </span>
            )}
          </div>
        </div>
      ))}


    </div>
  );
};

export default Notifications;
