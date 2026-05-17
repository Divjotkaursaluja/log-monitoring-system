// src/components/TrendChart.jsx
import { useEffect, useState } from "react";
import { fetchTrends } from "../services/api";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
} from "chart.js";

ChartJS.register(
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend
);

const TrendChart = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const refresh = () => fetchTrends().then(res => setData(res.data));
    refresh();
    const interval = window.setInterval(refresh, 3000);
    return () => window.clearInterval(interval);
  }, []);


  return (
    <div className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10 shadow-lg">
      <h2 className="text-lg mb-4">Error Trends</h2>

      {data.length === 0 ? (
        <p className="text-gray-400">No error trend data yet.</p>
      ) : (
        // {/* realtime data */}
        <Line
          data={{
            labels: data.map(d => d.time),
            datasets: [
              {
                label: "Errors",
                data: data.map(d => d.errors),
                borderColor: "#38bdf8",   // 🔥 visible line
                backgroundColor: "rgba(56,189,248,0.2)",
                tension: 0.4,             // smooth curve
                pointRadius: 4,
              },
            ],
          }}
          options={{
            plugins: {
              legend: {
                labels: { color: "#cbd5f5" }
              }
            },
            scales: {
              x: {
                ticks: { color: "#94a3b8" }
              },
              y: {
                ticks: { color: "#94a3b8" }
              }
            }
          }}
        />



      )}
    </div>
  );
};

export default TrendChart;
