import { useEffect, useState } from "react";
import { Analytics, getAnalytics } from "../api";
import { useAuth } from "../auth";

export function AnalyticsPage() {
  const { token } = useAuth();
  const [data, setData] = useState<Analytics | null>(null);
  const [start, setStart] = useState("2026-08-01");
  const [end, setEnd] = useState("2026-09-30");

  useEffect(() => {
    if (!token) return;
    getAnalytics(token, `${start}T00:00:00Z`, `${end}T23:59:59Z`).then(setData);
  }, [token, start, end]);

  const robotTotals = data?.episodes_per_day_per_robot.reduce(
    (acc, row) => {
      acc[row.robot_id] = (acc[row.robot_id] || 0) + row.count;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="mt-1 text-sm text-slate-400">Database-driven insights for operations</p>
      </div>

      <div className="flex flex-wrap gap-3">
        <input type="date" className="input max-w-xs" value={start} onChange={(e) => setStart(e.target.value)} />
        <input type="date" className="input max-w-xs" value={end} onChange={(e) => setEnd(e.target.value)} />
      </div>

      {!data ? (
        <div className="card p-12 text-center text-slate-400">Loading analytics...</div>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="card p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Request Fulfilment</h2>
            <div className="space-y-3">
              {Object.entries(data.request_fulfilment.status_counts).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <span className="capitalize text-slate-400">{status.replace("_", " ")}</span>
                  <span className="font-semibold text-white">{count}</span>
                </div>
              ))}
            </div>
            <div className="mt-6 rounded-xl bg-slate-800/50 p-4">
              <div className="text-xs text-slate-500">Median time submitted → delivered</div>
              <div className="mt-1 text-2xl font-bold text-brand-400">
                {data.request_fulfilment.median_hours_submitted_to_delivered != null
                  ? `${data.request_fulfilment.median_hours_submitted_to_delivered.toFixed(1)}h`
                  : "N/A"}
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">Top Tasks (Good Episodes)</h2>
            <div className="space-y-3">
              {data.top_tasks_by_good_episodes.map((t, i) => (
                <div key={t.task_name} className="flex items-center gap-3">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600/20 text-xs font-bold text-brand-400">
                    {i + 1}
                  </span>
                  <span className="flex-1 capitalize text-slate-300">{t.task_name}</span>
                  <span className="font-semibold text-white">{t.good_episode_count}</span>
                </div>
              ))}
              {data.top_tasks_by_good_episodes.length === 0 && (
                <p className="text-sm text-slate-500">No data in range</p>
              )}
            </div>
          </div>

          <div className="card p-6 lg:col-span-2">
            <h2 className="mb-4 text-lg font-semibold text-white">Episodes by Robot</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
              {robotTotals &&
                Object.entries(robotTotals)
                  .sort(([, a], [, b]) => b - a)
                  .map(([robot, count]) => (
                    <div key={robot} className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                      <div className="text-xs text-slate-500">{robot}</div>
                      <div className="mt-1 text-2xl font-bold text-white">{count}</div>
                    </div>
                  ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
