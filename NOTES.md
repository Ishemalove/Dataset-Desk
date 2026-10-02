# Design Notes — Dataset Request Desk

## 1. Design

### Data model

```
User ──< DatasetRequest ──< Assignment >── Episode
              │
              └──< StatusHistory
```

- **User** stores role (`client`, `operator`, `admin`) and hashed passwords.
- **Episode** is keyed by unique `episode_id` (normalized to uppercase). Imported from CSV; never duplicated thanks to a unique constraint.
- **DatasetRequest** belongs to a client; tracks task, count, deadline, status.
- **Assignment** links one episode to one request (unique on `episode_id`).
- **StatusHistory** append-only audit log for every status change.

State lives in PostgreSQL. The frontend is a thin client; all authorization and domain rules are enforced server-side.

### Hard decisions

1. **Import upsert vs skip:** Existing episodes with the same ID are updated if fields differ, skipped if identical. This makes re-import idempotent while allowing corrected CSV rows to propagate.

2. **Auto-transition on first assignment:** When an operator assigns episodes to a `submitted` request, it automatically moves to `in_progress`. This matches real ops workflow (work starts when episodes are picked) and avoids an extra manual step.

3. **Episode quality normalization:** `excellent` maps to `good`; unknown values are rejected. Task names are lowercased and whitespace-normalized so "Pick Cup" and "pick cup" match.

## 2. Deliberately left out / next steps

- Pagination on episode lists (currently capped at 500)
- Email notifications on status changes
- Request editing after submission
- Full status history UI (API exists, not shown in frontend)
- Real-time updates (stretch item — would use SSE)
- Background export jobs (stretch item)

With two more days: add pagination, status history timeline in the UI, and SSE for live request board updates.

## 3. Something that went wrong

Alembic enum types on PostgreSQL required explicit enum creation in the migration. SQLAlchemy's auto-generated enums conflicted when the same enum name was reused across columns. I resolved this by defining enums once in the migration and referencing them consistently. For tests, SQLite doesn't support PostgreSQL's `PERCENTILE_CONT`, so analytics tests were omitted from the SQLite test suite — analytics is tested manually against PostgreSQL via Docker.

## 4. Security

- Passwords hashed with bcrypt; never stored plain text.
- JWT tokens with configurable expiry; validated on every authenticated request.
- Role checks via FastAPI dependencies, not just UI hiding.
- CSV import validates robot IDs against an allowlist, sanitizes task names, rejects malformed rows.
- Input validation via Pydantic on all request bodies.

**Top two vulnerabilities I'd worry about:**

1. **JWT secret in env** — if leaked, tokens can be forged. Production needs a strong random secret rotated via secrets manager.
2. **CSV import DoS** — large file uploads could exhaust memory. Would add file size limits and streaming parse in production.

## 5. Scale

**At 10× users:** JWT auth and connection pooling handle this fine. Might need pgBouncer if concurrent operators spike.

**At 100× episodes (500K+):**

- Episode list/filter queries need pagination and covering indexes on `(task_name, quality, recorded_at)`.
- Analytics should move to pre-aggregated daily rollups (materialized view refreshed nightly).
- Assignment queries join episodes ↔ assignments — index on `assignments.episode_id` is critical (already present).

First thing to break: unbounded episode list endpoint without pagination.

## 6. AI tooling

Used Cursor AI assistant to scaffold the project structure, generate boilerplate (FastAPI routes, React components, Docker config), and draft this NOTES.md. All domain logic (status transitions, import rules, assignment constraints) was reviewed and understood. Tests were written to verify the critical paths.

## Import decisions (messy CSV)

| Case | Handling |
|---|---|
| Duplicate episode_id in file | Second occurrence skipped |
| Missing episode_id | Skipped |
| Unknown robot (arm-99) | Skipped |
| Invalid date | Skipped |
| Missing/invalid duration | Skipped |
| Empty quality | Skipped |
| "excellent" quality | Mapped to `good` |
| "Good"/"USABLE" casing | Normalized to lowercase |
| Whitespace in fields | Trimmed |
| Task name "  Pick Cup " | Normalized to `pick cup` |
| Future date (2031) | Skipped (outside 2020–2028 range) |
| Negative duration | Skipped |
| Duration > 600s | Skipped |
| Malformed rows (missing columns) | Skipped |
| Duplicate in DB (re-import) | Skipped if unchanged, updated if different |
