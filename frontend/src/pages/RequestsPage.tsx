import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createRequest, DatasetRequest, getRequests } from "../api";
import { useAuth } from "../auth";
import { StatusBadge } from "../components/StatusBadge";

export function RequestsPage() {
  const { user, token } = useAuth();
  const [requests, setRequests] = useState<DatasetRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    if (!token) return;
    getRequests(token)
      .then(setRequests)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(load, [token]);

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token) return;
    const fd = new FormData(e.currentTarget);
    try {
      await createRequest(token, {
        task_name: fd.get("task_name") as string,
        episodes_requested: Number(fd.get("episodes_requested")),
        deadline: new Date(fd.get("deadline") as string).toISOString(),
        notes: (fd.get("notes") as string) || undefined,
      });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  };

  const stats = {
    total: requests.length,
    active: requests.filter((r) => !["accepted", "rejected"].includes(r.status)).length,
    delivered: requests.filter((r) => r.status === "delivered").length,
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            {user?.role === "client" ? "My Requests" : "All Requests"}
          </h1>
          <p className="mt-1 text-sm text-slate-400">Track dataset fulfilment from submission to delivery</p>
        </div>
        {user?.role === "client" && (
          <button onClick={() => setShowForm(!showForm)} className="btn-primary">
            {showForm ? "Cancel" : "+ New Request"}
          </button>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: "Total", value: stats.total, color: "text-white" },
          { label: "Active", value: stats.active, color: "text-amber-400" },
          { label: "Awaiting Review", value: stats.delivered, color: "text-brand-400" },
        ].map((s) => (
          <div key={s.label} className="card p-5">
            <div className="text-xs font-medium uppercase tracking-wider text-slate-500">{s.label}</div>
            <div className={`mt-1 text-3xl font-bold ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="card grid gap-4 p-6 sm:grid-cols-2">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Task name</label>
            <input name="task_name" className="input" placeholder="pick cup" required />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Episodes requested</label>
            <input name="episodes_requested" type="number" min={1} className="input" defaultValue={10} required />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Deadline</label>
            <input name="deadline" type="datetime-local" className="input" required />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-slate-400">Notes</label>
            <input name="notes" className="input" placeholder="Optional details..." />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary">Submit Request</button>
          </div>
        </form>
      )}

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="card p-12 text-center text-slate-400">Loading requests...</div>
      ) : requests.length === 0 ? (
        <div className="card p-12 text-center">
          <p className="text-slate-400">No requests yet.</p>
          {user?.role === "client" && (
            <button onClick={() => setShowForm(true)} className="btn-primary mt-4">
              Create your first request
            </button>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs uppercase tracking-wider text-slate-500">
                <th className="px-6 py-4">Task</th>
                {user?.role !== "client" && <th className="px-6 py-4">Client</th>}
                <th className="px-6 py-4">Progress</th>
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Deadline</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {requests.map((req) => (
                <tr key={req.id} className="transition hover:bg-slate-800/30">
                  <td className="px-6 py-4">
                    <div className="font-medium capitalize text-slate-200">{req.task_name}</div>
                    <div className="text-xs text-slate-500">#{req.id}</div>
                  </td>
                  {user?.role !== "client" && (
                    <td className="px-6 py-4 text-slate-300">{req.client_name}</td>
                  )}
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-brand-500 transition-all"
                          style={{
                            width: `${Math.min(100, (req.assigned_count / req.episodes_requested) * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-slate-400">
                        {req.assigned_count}/{req.episodes_requested}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={req.status} />
                  </td>
                  <td className="px-6 py-4 text-slate-400">
                    {new Date(req.deadline).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/requests/${req.id}`}
                      className="text-sm font-medium text-brand-400 hover:text-brand-300"
                    >
                      View →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
