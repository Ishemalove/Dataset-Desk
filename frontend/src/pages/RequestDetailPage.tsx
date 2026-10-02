import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  assignEpisodes,
  changeStatus,
  DatasetRequest,
  Episode,
  getAssignedEpisodes,
  getEpisodes,
  getRequests,
  RequestStatus,
} from "../api";
// Episode list for assigned view is loaded via available filters
import { useAuth } from "../auth";
import { StatusBadge } from "../components/StatusBadge";

export function RequestDetailPage() {
  const { id } = useParams();
  const { user, token } = useAuth();
  const [request, setRequest] = useState<DatasetRequest | null>(null);
  const [available, setAvailable] = useState<Episode[]>([]);
  const [assigned, setAssigned] = useState<Episode[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [taskFilter, setTaskFilter] = useState("");
  const [qualityFilter, setQualityFilter] = useState("");

  const isOperator = user?.role === "operator" || user?.role === "admin";

  const load = async () => {
    if (!token || !id) return;
    try {
      const reqs = await getRequests(token);
      const req = reqs.find((r) => r.id === Number(id));
      if (!req) throw new Error("Request not found");
      setRequest(req);
      setTaskFilter((current) => current || req.task_name);
      setAssigned(await getAssignedEpisodes(token, req.id));

      if (isOperator) {
        const avail = await getEpisodes(token, {
          task_name: req.task_name,
          unassigned_only: true,
        });
        setAvailable(avail);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token, id]);

  useEffect(() => {
    if (!token || !id) return;
    const busy = assigned.some((e) => e.export_status === "pending" || e.export_status === "running");
    if (!busy) return;
    const timer = setInterval(() => {
      getAssignedEpisodes(token, Number(id)).then(setAssigned).catch(() => undefined);
    }, 2500);
    return () => clearInterval(timer);
  }, [token, id, assigned]);

  const handleStatus = async (status: RequestStatus) => {
    if (!token || !request) return;
    try {
      await changeStatus(token, request.id, status);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  };

  const handleAssign = async () => {
    if (!token || !request || selected.length === 0) return;
    try {
      await assignEpisodes(token, request.id, selected);
      setSelected([]);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    }
  };

  const filterEpisodes = () => {
    let eps = available;
    if (taskFilter) eps = eps.filter((e) => e.task_name.includes(taskFilter.toLowerCase()));
    if (qualityFilter) eps = eps.filter((e) => e.quality === qualityFilter);
    return eps;
  };

  if (loading) return <div className="card p-12 text-center text-slate-400">Loading...</div>;
  if (!request) return <div className="card p-12 text-center text-rose-400">Request not found</div>;

  const filtered = filterEpisodes();

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm text-slate-400 hover:text-slate-200">← Back to requests</Link>

      <div className="card p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold capitalize text-white">{request.task_name}</h1>
              <StatusBadge status={request.status} />
            </div>
            <p className="mt-2 text-sm text-slate-400">
              Request #{request.id} · {request.client_name} · Deadline{" "}
              {new Date(request.deadline).toLocaleString()}
            </p>
            {request.notes && <p className="mt-3 text-sm text-slate-300">{request.notes}</p>}
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-brand-400">
              {request.assigned_count}/{request.episodes_requested}
            </div>
            <div className="text-xs text-slate-500">episodes assigned</div>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {user?.role === "client" && request.status === "delivered" && (
            <>
              <button onClick={() => handleStatus("accepted")} className="btn-primary">
                Accept Delivery
              </button>
              <button onClick={() => handleStatus("rejected")} className="btn-secondary">
                Reject & Request Rework
              </button>
            </>
          )}
          {isOperator && request.status === "in_progress" && request.assigned_count >= request.episodes_requested && (
            <button onClick={() => handleStatus("delivered")} className="btn-primary">
              Mark as Delivered
            </button>
          )}
          {isOperator && request.status === "rejected" && (
            <button onClick={() => handleStatus("in_progress")} className="btn-primary">
              Resume Work
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {assigned.length > 0 && (
        <div className="card p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">Assigned episodes</h2>
          <div className="overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="bg-slate-900">
                <tr className="text-left text-xs uppercase text-slate-500">
                  <th className="px-4 py-3">Episode</th>
                  <th className="px-4 py-3">Robot</th>
                  <th className="px-4 py-3">Quality</th>
                  <th className="px-4 py-3">Export</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {assigned.map((ep) => (
                  <tr key={ep.id}>
                    <td className="px-4 py-2 font-mono text-xs text-slate-300">{ep.episode_id}</td>
                    <td className="px-4 py-2 text-slate-400">{ep.robot_id}</td>
                    <td className="px-4 py-2 text-slate-400">{ep.quality}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`badge ${
                          ep.export_status === "done"
                            ? "bg-emerald-500/20 text-emerald-300"
                            : ep.export_status === "failed"
                              ? "bg-rose-500/20 text-rose-300"
                              : ep.export_status === "running"
                                ? "bg-sky-500/20 text-sky-300"
                                : "bg-slate-500/20 text-slate-300"
                        }`}
                      >
                        {ep.export_status || "pending"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isOperator && ["submitted", "in_progress", "rejected"].includes(request.status) && (
        <div className="card p-6">
          <h2 className="mb-4 text-lg font-semibold text-white">Assign Episodes</h2>
          <div className="mb-4 flex flex-wrap gap-3">
            <input
              className="input max-w-xs"
              placeholder="Filter by task..."
              value={taskFilter}
              onChange={(e) => setTaskFilter(e.target.value)}
            />
            <select
              className="input max-w-xs"
              value={qualityFilter}
              onChange={(e) => setQualityFilter(e.target.value)}
            >
              <option value="">All qualities</option>
              <option value="good">Good</option>
              <option value="usable">Usable</option>
            </select>
            <button
              onClick={handleAssign}
              disabled={selected.length === 0}
              className="btn-primary"
            >
              Assign {selected.length > 0 ? `(${selected.length})` : ""}
            </button>
          </div>
          <div className="max-h-80 overflow-y-auto rounded-xl border border-slate-800">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-900">
                <tr className="text-left text-xs uppercase text-slate-500">
                  <th className="px-4 py-3 w-10"></th>
                  <th className="px-4 py-3">Episode</th>
                  <th className="px-4 py-3">Robot</th>
                  <th className="px-4 py-3">Quality</th>
                  <th className="px-4 py-3">Recorded</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {filtered.map((ep) => (
                  <tr key={ep.id} className="hover:bg-slate-800/40">
                    <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selected.includes(ep.id)}
                        onChange={(e) =>
                          setSelected((s) =>
                            e.target.checked ? [...s, ep.id] : s.filter((id) => id !== ep.id)
                          )
                        }
                        className="rounded border-slate-600"
                      />
                    </td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-300">{ep.episode_id}</td>
                    <td className="px-4 py-2 text-slate-400">{ep.robot_id}</td>
                    <td className="px-4 py-2">
                      <span
                        className={`badge ${
                          ep.quality === "good"
                            ? "bg-emerald-500/20 text-emerald-300"
                            : "bg-amber-500/20 text-amber-300"
                        }`}
                      >
                        {ep.quality}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-500">
                      {new Date(ep.recorded_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <p className="p-6 text-center text-sm text-slate-500">No matching unassigned episodes</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
