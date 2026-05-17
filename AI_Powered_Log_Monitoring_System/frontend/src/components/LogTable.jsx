const levelStyles = {
  ERROR: "bg-red-500/10 text-red-200 ring-red-500/30",
  WARNING: "bg-yellow-400/10 text-yellow-100 ring-yellow-300/30",
  INFO: "bg-green-500/10 text-green-200 ring-green-500/30",
};

const formatTimestamp = (value) => {
  if (!value) return "Pending";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
};

const LogTable = ({ logs, loading }) => {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-950/70 shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Live Application Logs</h2>
          <p className="text-sm text-slate-400">Latest records stored by the FastAPI backend</p>
        </div>
        <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-xs font-medium text-cyan-200 ring-1 ring-cyan-300/20">
          Auto refresh
        </span>
      </div>

      <div className="max-h-[520px] overflow-auto">
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead className="sticky top-0 bg-slate-900 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-5 py-3 font-semibold">Timestamp</th>
              <th className="px-5 py-3 font-semibold">Severity</th>
              <th className="px-5 py-3 font-semibold">Service</th>
              <th className="px-5 py-3 font-semibold">AI Prediction</th>
              <th className="px-5 py-3 font-semibold">Anomaly</th>
              <th className="px-5 py-3 font-semibold">Log Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850">
            {loading && (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan="6">
                  Loading logs...
                </td>
              </tr>
            )}

            {!loading && logs.length === 0 && (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan="6">
                  No logs have been stored yet.
                </td>
              </tr>
            )}

            {!loading &&
              logs.map((log) => (
                <tr key={log.id ?? `${log.timestamp}-${log.message}`} className="hover:bg-slate-900/70">
                  <td className="whitespace-nowrap px-5 py-4 text-slate-300">
                    {formatTimestamp(log.timestamp)}
                  </td>
                  <td className="px-5 py-4">
                    <span
                      className={`inline-flex min-w-20 justify-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                        levelStyles[log.level] || "bg-slate-700 text-slate-200 ring-slate-600"
                      }`}
                    >
                      {log.level}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-200">
                    {log.service_name}
                  </td>
                  <td className="whitespace-nowrap px-5 py-4 text-slate-300">
                    <div className="font-medium text-slate-100">
                      {log.predicted_category || "Pending"}
                    </div>
                    <div className="text-xs text-slate-400">
                      {log.predicted_severity || "unknown"}
                      {typeof log.confidence === "number"
                        ? ` · ${(log.confidence * 100).toFixed(0)}%`
                        : ""}
                    </div>
                  </td>
                  <td className="whitespace-nowrap px-5 py-4">
                    <span
                      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${
                        log.is_anomaly
                          ? "bg-red-500/10 text-red-200 ring-red-500/30"
                          : "bg-slate-700/60 text-slate-200 ring-slate-600"
                      }`}
                    >
                      {log.is_anomaly ? "Yes" : "No"}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-slate-300">{log.message}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};

export default LogTable;
