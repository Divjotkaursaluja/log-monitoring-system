import CountCards from "../components/CountCards";
import LogTable from "../components/LogTable";
import useLogs from "../hooks/useLogs";

const Dashboard = () => {
  const { logs, metrics, loading, error, lastUpdated, refresh } = useLogs(3000);

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="flex flex-col gap-4 border-b border-slate-800 pb-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
              Civic Issue System Observability
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">
              AI Powered Log Monitoring System
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Real-time view of logs flowing from app.log into FastAPI and MySQL.
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
          </div>
        </header>

        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            Backend connection issue: {error}
          </div>
        )}

        <CountCards metrics={metrics} />
        <LogTable logs={logs} loading={loading} />
      </div>
    </main>
  );
};

export default Dashboard;
