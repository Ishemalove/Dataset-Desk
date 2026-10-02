# Dataset Request Desk

Internal platform for managing robotics dataset requests.

## Run locally (no Docker)

PostgreSQL 17 is already running as the Windows service `postgresql-x64-17`. User **postgres**, password **love**.

**Create the database once** (PowerShell):

If it already exists, you can ignore the error and continue. `python scripts/run_local.py` will also create `dataset_desk` if it is missing.

**Terminal 1 — API** (migrations, seed users + episodes, then uvicorn):

```powershell
cd backend
pip install -r requirements.txt
python scripts/run_local.py
```

**Terminal 2 — UI:**

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api` to the backend on port 8000.

- API: http://localhost:8000
- Health: http://localhost:8000/health (shows `"database": "ok"` when Postgres is connected)
- API docs: http://localhost:8000/docs

## Seed user credentials

| Email | Password | Role |
|---|---|---|
| admin@example.com | admin123 | Admin |
| ops1@example.com | ops123 | Operator |
| ops2@example.com | ops123 | Operator |
| client-a@example.com | client123 | Client (Acme Robotics) |
| client-b@example.com | client123 | Client (Beta Labs) |

## Running tests

```powershell
cd backend
pip install -r requirements.txt
pytest -v
```

## Architecture

- **Backend:** FastAPI + SQLAlchemy + Alembic + PostgreSQL
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Auth:** JWT bearer tokens, bcrypt password hashing
- **Export jobs:** assigning an episode queues a background export (2–5s, ~20% fail, up to 3 retries). Status is stored on the assignment row and shown on the request detail page.


