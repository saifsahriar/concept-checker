# Concept Checker

Concept Checker is a small full-stack MVP for checking whether a student really understands a concept or is only repeating a definition.

## Structure

- `backend/` FastAPI service with auth, session flow, and NIM integration
- `frontend/` React + Vite SPA
- `backend/sql/schema.sql` Postgres schema and RLS

## What is in place

- Login/signup flow through Supabase Auth on the frontend
- Supabase JWT verification on the backend
- Session creation, initial explanation, follow-up questions, and final evaluation APIs
- NVIDIA NIM integration with a local fallback when the key is not configured
- Session history and per-session detail views

## Local development

Backend:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

Backend:

- `DATABASE_URL` optional for Postgres; if missing, the app uses an in-memory store
- `SUPABASE_URL` optional; if omitted, the backend derives it from the Supabase `DATABASE_URL`
- `SUPABASE_JWT_SECRET` optional for JWT verification
- `NIM_API_KEY` optional for NVIDIA NIM
- `NIM_BASE_URL` defaults to `https://integrate.api.nvidia.com/v1`
- `NIM_MODEL` defaults to `nvidia/llama-3.3-nemotron-super-49b-v1`
- `CORS_ORIGINS` defaults to `http://localhost:5173`

Frontend:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL` defaults to `http://localhost:8000`

## Notes

The database schema is already included for Supabase/Postgres deployment, but the backend can still run locally without Postgres while the UI and API flow are being built out.
