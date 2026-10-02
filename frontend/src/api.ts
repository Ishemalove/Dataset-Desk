const API_BASE = import.meta.env.VITE_API_URL || "";

export type UserRole = "client" | "operator" | "admin";
export type RequestStatus = "submitted" | "in_progress" | "delivered" | "accepted" | "rejected";
export type EpisodeQuality = "good" | "usable" | "bad";

export interface User {
  id: number;
  email: string;
  role: UserRole;
  name: string;
  organisation: string | null;
  is_active: boolean;
}

export interface DatasetRequest {
  id: number;
  client_id: number;
  client_name: string;
  task_name: string;
  episodes_requested: number;
  deadline: string;
  notes: string | null;
  status: RequestStatus;
  assigned_count: number;
  created_at: string;
  updated_at: string;
}

export interface Episode {
  id: number;
  episode_id: string;
  robot_id: string;
  task_name: string;
  recorded_at: string;
  duration_seconds: number;
  operator_name: string;
  quality: EpisodeQuality;
  assigned: boolean;
  export_status?: "pending" | "running" | "done" | "failed" | null;
}

export interface ImportResult {
  imported: number;
  skipped: number;
  updated: number;
  errors: string[];
}

export interface Analytics {
  episodes_per_day_per_robot: { date: string; robot_id: string; count: number }[];
  request_fulfilment: {
    status_counts: Record<string, number>;
    median_hours_submitted_to_delivered: number | null;
  };
  top_tasks_by_good_episodes: { task_name: string; good_episode_count: number }[];
}

function authHeaders(token: string) {
  return { Authorization: `Bearer ${token}` };
}

export async function login(email: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Invalid credentials");
  const data = await res.json();
  return data.access_token;
}

export async function getMe(token: string): Promise<User> {
  const res = await fetch(`${API_BASE}/api/auth/me`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Session expired");
  return res.json();
}

export async function getRequests(token: string): Promise<DatasetRequest[]> {
  const res = await fetch(`${API_BASE}/api/requests`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to load requests");
  return res.json();
}

export async function createRequest(
  token: string,
  data: { task_name: string; episodes_requested: number; deadline: string; notes?: string }
): Promise<DatasetRequest> {
  const res = await fetch(`${API_BASE}/api/requests`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create request");
  }
  return res.json();
}

export async function changeStatus(token: string, requestId: number, status: RequestStatus) {
  const res = await fetch(`${API_BASE}/api/requests/${requestId}/status`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(typeof err.detail === "string" ? err.detail : "Status change failed");
  }
  return res.json();
}

export async function getEpisodes(
  token: string,
  params: { task_name?: string; quality?: string; unassigned_only?: boolean }
): Promise<Episode[]> {
  const qs = new URLSearchParams();
  if (params.task_name) qs.set("task_name", params.task_name);
  if (params.quality) qs.set("quality", params.quality);
  if (params.unassigned_only) qs.set("unassigned_only", "true");
  const res = await fetch(`${API_BASE}/api/episodes?${qs}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to load episodes");
  return res.json();
}

export async function getAssignedEpisodes(token: string, requestId: number): Promise<Episode[]> {
  const res = await fetch(`${API_BASE}/api/requests/${requestId}/episodes`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to load assigned episodes");
  return res.json();
}

export async function assignEpisodes(token: string, requestId: number, episodeIds: number[]) {
  const res = await fetch(`${API_BASE}/api/requests/${requestId}/assign`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify({ episode_ids: episodeIds }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(typeof err.detail === "string" ? err.detail : "Assignment failed");
  }
  return res.json();
}

export async function importEpisodes(token: string, file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/episodes/import`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  if (!res.ok) throw new Error("Import failed");
  return res.json();
}

export async function getAnalytics(token: string, start: string, end: string): Promise<Analytics> {
  const qs = new URLSearchParams({ start_date: start, end_date: end });
  const res = await fetch(`${API_BASE}/api/analytics?${qs}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to load analytics");
  return res.json();
}

export async function getUsers(token: string): Promise<User[]> {
  const res = await fetch(`${API_BASE}/api/auth/users`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

export async function createUser(
  token: string,
  data: { email: string; password: string; role: UserRole; name: string; organisation?: string }
) {
  const res = await fetch(`${API_BASE}/api/auth/users`, {
    method: "POST",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Failed to create user");
  }
  return res.json();
}

export async function updateUser(token: string, userId: number, data: Partial<User>) {
  const res = await fetch(`${API_BASE}/api/auth/users/${userId}`, {
    method: "PATCH",
    headers: { ...authHeaders(token), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update user");
  return res.json();
}
