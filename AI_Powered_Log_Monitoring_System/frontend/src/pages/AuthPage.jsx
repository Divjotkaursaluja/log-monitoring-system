import { useState } from "react";
import { login, signup } from "../services/api";

const AuthPage = ({ onAuthenticated }) => {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    organization_name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateField = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const submit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response =
        mode === "signup"
          ? await signup(form)
          : await login({ email: form.email, password: form.password });
      onAuthenticated(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4 text-white">
      <section className="w-full max-w-md rounded-lg border border-slate-800 bg-slate-900/80 p-6 shadow-xl">
        <p className="text-sm font-medium uppercase tracking-wide text-cyan-300">
          Multi-tenant observability
        </p>
        <h1 className="mt-2 text-2xl font-semibold">AI Powered Log Monitoring System</h1>

        <div className="mt-6 grid grid-cols-2 rounded-md border border-slate-700 p-1">
          {["login", "signup"].map((item) => (
            <button
              className={`rounded px-3 py-2 text-sm font-semibold ${
                mode === item ? "bg-cyan-500 text-slate-950" : "text-slate-300"
              }`}
              key={item}
              onClick={() => setMode(item)}
              type="button"
            >
              {item === "login" ? "Login" : "Signup"}
            </button>
          ))}
        </div>

        <form className="mt-6 space-y-4" onSubmit={submit}>
          {mode === "signup" && (
            <label className="block text-sm text-slate-300">
              Organization
              <input
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
                name="organization_name"
                onChange={updateField}
                required
                value={form.organization_name}
              />
            </label>
          )}

          <label className="block text-sm text-slate-300">
            Email
            <input
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
              name="email"
              onChange={updateField}
              required
              type="email"
              value={form.email}
            />
          </label>

          <label className="block text-sm text-slate-300">
            Password
            <input
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-cyan-400"
              minLength={mode === "signup" ? 8 : 1}
              name="password"
              onChange={updateField}
              required
              type="password"
              value={form.password}
            />
          </label>

          {error && (
            <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              {error}
            </div>
          )}

          <button
            className="w-full rounded-md bg-cyan-500 px-4 py-2 font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {loading ? "Please wait..." : mode === "login" ? "Login" : "Create organization"}
          </button>
        </form>
      </section>
    </main>
  );
};

export default AuthPage;
