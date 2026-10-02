import { FormEvent, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth";

const DEMO_ACCOUNTS = [
  { email: "client-a@example.com", password: "client123", role: "Client" },
  { email: "ops1@example.com", password: "ops123", role: "Operator" },
  { email: "admin@example.com", password: "admin123", role: "Admin" },
];

export function LoginPage() {
  const { user, login, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!loading && user) return <Navigate to="/" replace />;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
    } catch {
      setError("Invalid email or password");
    } finally {
      setSubmitting(false);
    }
  };

  const quickLogin = async (acc: (typeof DEMO_ACCOUNTS)[0]) => {
    setEmail(acc.email);
    setPassword(acc.password);
    setSubmitting(true);
    try {
      await login(acc.email, acc.password);
    } catch {
      setError("Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 text-xl font-bold shadow-lg shadow-brand-600/30">
            DR
          </div>
          <h1 className="text-2xl font-bold text-white">Dataset Request Desk</h1>
          <p className="mt-2 text-sm text-slate-400">Internal platform for robotics data collection</p>
        </div>

        <form onSubmit={handleSubmit} className="card space-y-4 p-6">
          {error && (
            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
              {error}
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Email</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary w-full" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="mt-6 card p-4">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-500">Demo accounts</p>
          <div className="space-y-2">
            {DEMO_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                onClick={() => quickLogin(acc)}
                disabled={submitting}
                className="flex w-full items-center justify-between rounded-xl border border-slate-800 bg-slate-900/40 px-4 py-2.5 text-left text-sm transition hover:border-slate-700 hover:bg-slate-800/60"
              >
                <span className="text-slate-300">{acc.role}</span>
                <span className="text-xs text-slate-500">{acc.email}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
