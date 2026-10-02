import { useEffect, useRef, useState } from "react";
import { Episode, getEpisodes, importEpisodes, ImportResult } from "../api";
import { useAuth } from "../auth";

export function EpisodesPage() {
  const { token } = useAuth();
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [taskFilter, setTaskFilter] = useState("");
  const [qualityFilter, setQualityFilter] = useState("");
  const [unassignedOnly, setUnassignedOnly] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(true);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = () => {
    if (!token) return;
    getEpisodes(token, {
      task_name: taskFilter || undefined,
      quality: qualityFilter || undefined,
      unassigned_only: unassignedOnly,
    })
      .then(setEpisodes)
      .finally(() => setLoading(false));
  };

  useEffect(load, [token, taskFilter, qualityFilter, unassignedOnly]);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !token) return;
    const result = await importEpisodes(token, file);
    setImportResult(result);
    load();
    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Episode Library</h1>
          <p className="mt-1 text-sm text-slate-400">Browse and import recording sessions</p>
        </div>
        <label className="btn-primary cursor-pointer">
          Import CSV
          <input ref={fileRef} type="file" accept=".csv" className="hidden" onChange={handleImport} />
        </label>
      </div>

      {importResult && (
        <div className="card p-4">
          <div className="flex gap-6 text-sm">
            <span className="text-emerald-400">Imported: {importResult.imported}</span>
            <span className="text-amber-400">Updated: {importResult.updated}</span>
            <span className="text-slate-400">Skipped: {importResult.skipped}</span>
          </div>
          {importResult.errors.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-slate-500">
                {importResult.errors.length} issues reported
              </summary>
              <ul className="mt-2 max-h-40 overflow-y-auto text-xs text-slate-500">
                {importResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <input
          className="input max-w-xs"
          placeholder="Filter by task..."
          value={taskFilter}
          onChange={(e) => setTaskFilter(e.target.value)}
        />
        <select className="input max-w-xs" value={qualityFilter} onChange={(e) => setQualityFilter(e.target.value)}>
          <option value="">All qualities</option>
          <option value="good">Good</option>
          <option value="usable">Usable</option>
          <option value="bad">Bad</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-slate-400">
          <input
            type="checkbox"
            checked={unassignedOnly}
            onChange={(e) => setUnassignedOnly(e.target.checked)}
            className="rounded border-slate-600"
          />
          Unassigned only
        </label>
      </div>

      <div className="card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading...</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left text-xs uppercase text-slate-500">
                <th className="px-6 py-4">Episode ID</th>
                <th className="px-6 py-4">Task</th>
                <th className="px-6 py-4">Robot</th>
                <th className="px-6 py-4">Quality</th>
                <th className="px-6 py-4">Duration</th>
                <th className="px-6 py-4">Operator</th>
                <th className="px-6 py-4">Assigned</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {episodes.map((ep) => (
                <tr key={ep.id} className="hover:bg-slate-800/30">
                  <td className="px-6 py-3 font-mono text-xs text-slate-300">{ep.episode_id}</td>
                  <td className="px-6 py-3 capitalize text-slate-200">{ep.task_name}</td>
                  <td className="px-6 py-3 text-slate-400">{ep.robot_id}</td>
                  <td className="px-6 py-3">
                    <span
                      className={`badge ${
                        ep.quality === "good"
                          ? "bg-emerald-500/20 text-emerald-300"
                          : ep.quality === "usable"
                            ? "bg-amber-500/20 text-amber-300"
                            : "bg-rose-500/20 text-rose-300"
                      }`}
                    >
                      {ep.quality}
                    </span>
                  </td>
                  <td className="px-6 py-3 text-slate-400">{ep.duration_seconds}s</td>
                  <td className="px-6 py-3 text-slate-400">{ep.operator_name}</td>
                  <td className="px-6 py-3">
                    {ep.assigned ? (
                      <span className="text-xs text-brand-400">Yes</span>
                    ) : (
                      <span className="text-xs text-slate-600">No</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
