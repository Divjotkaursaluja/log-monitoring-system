// src/components/TopIssues.jsx
import { useEffect, useState } from "react";
import { fetchIssues } from "../services/api";


const TopIssues = () => {
  const [issues, setIssues] = useState([]);

  useEffect(() => {
    fetchIssues().then(res => setIssues(res.data));
  }, []);

  return (
    <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10 shadow-lg">
      <h2 className="text-lg mb-4">Top Issues</h2>

      {/* realtime data */}
      {issues.map((issue, i) => (
        <div key={i} className="flex justify-between py-2 border-b border-slate-700">
          <span>{issue.service}</span>
          <span className="text-red-400">{issue.error_count}</span>
        </div>
      ))}

    </div>
  );
};

export default TopIssues;