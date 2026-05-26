import CountCards from "../components/CountCards";
import LogTable from "../components/LogTable";
import useLogs from "../hooks/useLogs";
import TrendChart from "../components/TrendChart";
import Notifications from "../components/Notifications";
import TopIssues from "../components/TopIssues";
import HealthStatus from "../components/HealthStatus";
import AlertsPanel from "../components/AlertsPanel";
import AlertHistory from "../components/AlertHistory";
const Dashboard = ({ session, onLogout }) => {
  const { logs, metrics, loading, error, lastUpdated, refresh } = useLogs(3000);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-slate-800 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
              {session?.organization?.name || "Organization"} Observability
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">
              AI Powered Log Monitoring System
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Real-time view of logs flowing from app.log into FastAPI and MySQL.
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Organization key: {session?.organization?.organization_key}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
            <span>
              Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "waiting"}
            </span>
            <button
              className="rounded-md bg-cyan-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-400"
              onClick={refresh}
              type="button"
            >
              Refresh
            </button>
            <button
              className="rounded-md border border-slate-700 px-4 py-2 font-semibold text-slate-200 transition hover:border-slate-500"
              onClick={onLogout}
              type="button"
            >
              Logout
            </button>
          </div>
        </header>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            Backend connection issue: {error}
          </div>
        )}

        <CountCards metrics={metrics} />

<div className="grid gap-4 lg:grid-cols-2">
  <HealthStatus />
  <AlertsPanel />
</div>

<TrendChart />

<LogTable logs={logs} loading={loading} />

<AlertHistory />

<div className="grid gap-4 lg:grid-cols-2">
  <TopIssues />
  <Notifications />
</div>
      </div>
    </main>
  );
};

export default Dashboard;
