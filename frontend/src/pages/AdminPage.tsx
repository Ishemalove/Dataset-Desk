import { FormEvent, useEffect, useState } from "react";
import { createUser, getUsers, updateUser, User, UserRole } from "../api";
import { useAuth } from "../auth";

export function AdminPage() {
  const { token } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const load = () => {
    if (!token) return;
    getUsers(token).then(setUsers).catch((e) => setError(e.message));
  };

  useEffect(load, [token]);

  const handleCreate = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!token) return;
    const fd = new FormData(e.currentTarget);
    try {
      await createUser(token, {
        email: fd.get("email") as string,
        password: fd.get("password") as string,
        role: fd.get("role") as UserRole,
        name: fd.get("name") as string,
        organisation: (fd.get("organisation") as string) || undefined,
      });
      setShowForm(false);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    }
  };

  const toggleActive = async (user: User) => {
    if (!token) return;
    await updateUser(token, user.id, { is_active: !user.is_active });
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="mt-1 text-sm text-slate-400">Create and manage platform accounts</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? "Cancel" : "+ Add User"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={handleCreate} className="card grid gap-4 p-6 sm:grid-cols-2">
          <input name="name" className="input" placeholder="Full name" required />
          <input name="email" type="email" className="input" placeholder="Email" required />
          <input name="password" type="password" className="input" placeholder="Password" required />
          <select name="role" className="input" required>
            <option value="client">Client</option>
            <option value="operator">Operator</option>
            <option value="admin">Admin</option>
          </select>
          <input name="organisation" className="input sm:col-span-2" placeholder="Organisation (optional)" />
          <div className="sm:col-span-2">
            <button type="submit" className="btn-primary">Create User</button>
          </div>
        </form>
      )}

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-xs uppercase text-slate-500">
              <th className="px-6 py-4">Name</th>
              <th className="px-6 py-4">Email</th>
              <th className="px-6 py-4">Role</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-800/30">
                <td className="px-6 py-4 text-slate-200">{u.name}</td>
                <td className="px-6 py-4 text-slate-400">{u.email}</td>
                <td className="px-6 py-4 capitalize text-slate-400">{u.role}</td>
                <td className="px-6 py-4">
                  <span
                    className={`badge ${u.is_active ? "bg-emerald-500/20 text-emerald-300" : "bg-slate-700 text-slate-400"}`}
                  >
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button onClick={() => toggleActive(u)} className="text-xs text-brand-400 hover:text-brand-300">
                    {u.is_active ? "Deactivate" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
