import { RequestStatus } from "../api";

const styles: Record<RequestStatus, string> = {
  submitted: "bg-slate-700 text-slate-200",
  in_progress: "bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30",
  delivered: "bg-brand-500/20 text-brand-300 ring-1 ring-brand-500/30",
  accepted: "bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30",
  rejected: "bg-rose-500/20 text-rose-300 ring-1 ring-rose-500/30",
};

const labels: Record<RequestStatus, string> = {
  submitted: "Submitted",
  in_progress: "In Progress",
  delivered: "Delivered",
  accepted: "Accepted",
  rejected: "Rejected",
};

export function StatusBadge({ status }: { status: RequestStatus }) {
  return <span className={`badge ${styles[status]}`}>{labels[status]}</span>;
}
