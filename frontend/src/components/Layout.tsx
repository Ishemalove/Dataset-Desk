import { Link, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

export function Layout() {
  const { user, logout } = useAuth();
  const location = useLocation();

  const nav = [
    { to: "/", label: "Requests", roles: ["client", "operator", "admin"] },
    { to: "/episodes", label: "Episodes", roles: ["operator", "admin"] },
    { to: "/analytics", label: "Analytics", roles: ["operator", "admin"] },
    { to: "/admin", label: "Users", roles: ["admin"] },
  ].filter((n) => user && n.roles.includes(user.role));

  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-sm font-bold">
                DR
              </div>
              <div>
                <div className="text-sm font-semibold text-white">Dataset Request Desk</div>
                <div className="text-xs text-slate-400">Robotics data operations</div>
              </div>
            </Link>
            <nav className="hidden gap-1 md:flex">
              {nav.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                    location.pathname === item.to
                      ? "bg-slate-800 text-white"
                      : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <div className="text-sm font-medium text-slate-200">{user?.name}</div>
              <div className="text-xs capitalize text-slate-500">{user?.role}</div>
            </div>
            <button onClick={logout} className="btn-secondary text-xs">
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
