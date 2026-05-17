const cards = [
  { key: "total_logs", label: "Total Logs", accent: "border-cyan-400/50 text-cyan-200" },
  { key: "total_errors", label: "Total Errors", accent: "border-red-400/50 text-red-200" },
  { key: "total_warnings", label: "Total Warnings", accent: "border-yellow-300/60 text-yellow-100" },
  { key: "total_info", label: "Total Info Logs", accent: "border-green-400/50 text-green-200" },
  { key: "active_alerts", label: "Active Alerts", accent: "border-orange-400/50 text-orange-200" },
  { key: "critical_incidents", label: "Critical Incidents", accent: "border-rose-400/50 text-rose-200" },
];
const CountCards = ({ metrics }) => {
  return (
    <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
      {cards.map((card) => (
        <div
          key={card.key}
          className={`rounded-lg border bg-slate-900/80 p-5 shadow-sm ${card.accent}`}
        >
          <p className="text-sm font-medium text-slate-400">{card.label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
            {metrics?.[card.key] ?? 0}
          </p>
        </div>
      ))}
    </section>
  );
};

export default CountCards;
