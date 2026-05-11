// src/components/Notifications.jsx
import { useEffect, useState } from "react";
import { fetchNotifications } from "../services/api";

const Notifications = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetchNotifications().then(res => setData(res.data));
  }, []);

  return (
    <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10 shadow-lg">
      <h2 className="text-lg mb-4">Notifications</h2>

      {/* realtime data */}
      {data.map((n, i) => (
        <div key={i} className="text-sm py-2 border-b border-slate-700">
          {n.message}
        </div>
      ))}


    </div>
  );
};

export default Notifications;