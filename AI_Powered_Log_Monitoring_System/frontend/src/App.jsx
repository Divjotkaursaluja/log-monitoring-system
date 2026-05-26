import { useEffect, useState } from "react";
import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import { fetchMe } from "./services/api";

const App = () => {
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem("session");
    return stored ? JSON.parse(stored) : null;
  });
  const [checking, setChecking] = useState(Boolean(localStorage.getItem("access_token")));

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setChecking(false);
      return;
    }

    fetchMe()
      .then((response) => {
        const nextSession = response.data;
        localStorage.setItem("session", JSON.stringify(nextSession));
        setSession(nextSession);
      })
      .catch(() => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("session");
        setSession(null);
      })
      .finally(() => setChecking(false));
  }, []);

  const handleAuthenticated = (payload) => {
    localStorage.setItem("access_token", payload.access_token);
    localStorage.setItem("session", JSON.stringify(payload));
    setSession(payload);
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("session");
    setSession(null);
  };

  if (checking) {
    return <main className="min-h-screen bg-slate-950 text-white" />;
  }

  if (!session) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  return <Dashboard onLogout={logout} session={session} />;
};

export default App;
