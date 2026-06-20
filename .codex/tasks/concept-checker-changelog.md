# Concept Checker Change Log

This file is append-only and records implementation changes separately from the plan.

## 2026-06-20

### Scaffold started
- Added repo-level scaffolding for the MVP rather than waiting for a perfect first pass.
- Created the backend app structure with settings, JWT auth, a repository abstraction, session flow service, FastAPI routes, and a Supabase/Postgres schema file with RLS policies.
- Added a NIM client wrapper that uses the configured NVIDIA endpoint when available and falls back to deterministic local analysis so the app can still be exercised without secrets.
- Added the frontend Vite + React + TypeScript shell with Supabase auth hooks, API helpers, a linear session flow UI, session history, and a more intentional visual treatment.
- Added local development docs and environment examples for both apps.

### Scaffold sanity pass
- Tightened the frontend session-switch behavior so explanation drafts and follow-up answers reset when the active session changes.
- Hid the follow-up form once a session reaches the complete state, which keeps the final report read-only after submission.
- Verified the Python backend sources with `python3 -m compileall backend/app` to catch syntax issues early.

### Backend startup fix
- Removed the eager Postgres connection from FastAPI lifespan startup so the API can boot even when the database host is temporarily unreachable.
- Kept database connection attempts lazy inside the repository methods that actually need them, which lets `/api/health` come up without waiting on Postgres.

### Database health check
- Added a dedicated `/api/db-health` route so API uptime and database reachability can be checked separately.
- Exposed a minimal repository health check method for both the in-memory and Postgres implementations.

### Auth feedback fix
- Updated the signup/signin flow to show a visible success message instead of appearing to do nothing.
- Added an explicit note for the common Supabase case where signup succeeds but email confirmation is still required before the user gets a session.

### Auth verification fallback
- Updated backend auth verification to try the legacy shared-secret path first and then fall back to Supabase JWKS verification from the project URL.
- Derived the Supabase project URL from `DATABASE_URL` when needed so the backend can verify signed tokens without requiring extra auth config.

### NIM timeout fallback
- Made the backend fail soft when the NVIDIA NIM chat completion call times out or errors, so saving an explanation still works even if the model endpoint is unavailable.
- The initial gap analysis and final evaluation now fall back to deterministic local logic instead of returning a 500.

### Output formatting cleanup
- Normalized structured model outputs into plain human-readable text before saving them to the database.
- Added frontend display cleanup so older saved analyses that already contain list/dict-like text render in a readable form.

### New conversation action
- Added a `New conversation` UI action that clears the active session state and returns the user to the concept entry flow.
- Kept the implementation UI-only so no schema change was needed.

### Prompt rewrite
- Replaced the vague NIM system prompts with the stronger Concept Checker prompts for the gap/follow-up generator and final evaluator.
- Aligned the user message payloads to the new prompt wording and explicit field names from the workflow spec.
