# Concept Checker MVP Plan

## Goal
Build a simple full-stack MVP for Concept Checker that matches the PRD:
- React + Vite + TypeScript frontend
- FastAPI backend
- Supabase Auth for login/signup
- Supabase Postgres for persistence
- NVIDIA NIM for all LLM calls
- Session history and final evaluation report

The MVP should stay intentionally small: thin frontend, backend-owned business logic, and a clear question-flow that checks conceptual understanding rather than memorization.

## Assumptions
- The repository is currently empty enough that we are scaffolding from scratch.
- We will keep the first version local/dev-friendly and focus on structure, correctness, and clean boundaries.
- We will not add features the PRD explicitly excludes, such as analytics, sharing, gamification, vector search, or multi-user collaboration.

## Implementation Plan

### 1. Scaffold the project structure
Create a minimal monorepo layout with separate frontend and backend apps plus shared docs/config.
- `frontend/` for the Vite SPA
- `backend/` for the FastAPI service
- root README and environment examples

Reasoning:
- The PRD is very clear about the frontend/backend split, so separate app folders keep that boundary obvious.
- This makes it easier to deploy the two halves independently later.

### 2. Build the backend foundation first
Set up FastAPI with a clean app structure, CORS, settings loading, and health checks.
- central config via environment variables
- request logging and error shaping
- API routes grouped by domain: auth/session/history/analysis

Reasoning:
- The backend owns the core business logic, database writes, and LLM calls.
- A stable API contract will make the frontend simpler and keep the SPA thin.

### 3. Add Supabase JWT verification
Implement backend authentication dependency that:
- reads the bearer token from requests
- verifies the Supabase JWT using the project secret
- extracts the authenticated user id
- rejects unauthenticated requests consistently

Reasoning:
- The PRD says there is no separate auth system.
- Every protected route must trust the same identity source, and the backend should never accept user identity from the client body.

### 4. Design and implement the database schema
Create tables and relationships for:
- `users`
- `sessions`
- `responses`
- `analysis`

Include:
- timestamps
- foreign keys
- understanding score on sessions
- stage values for responses
- RLS policies for user-scoped access

Reasoning:
- The schema is small, so we should make it explicit and well constrained rather than ad hoc.
- RLS should be enabled as a second line of defense even though the backend is the primary gatekeeper.

### 5. Implement the concept-check flow endpoints
Add backend endpoints for the user journey:
- create a new session with a concept
- save the initial explanation
- generate/store follow-up questions
- accept follow-up answers
- generate/store final evaluation
- fetch a session detail
- list prior sessions for history

Reasoning:
- This mirrors the PRD workflow directly and keeps the state machine easy to reason about.
- The backend should own the session progression so the frontend only renders the current step.

### 6. Wire in NVIDIA NIM for analysis
Implement backend service code for the LLM calls using:
- `nvidia/llama-3.3-nemotron-super-49b-v1`
- `https://integrate.api.nvidia.com/v1`

The LLM should handle:
- initial gap analysis
- targeted follow-up question generation
- final evaluation and score

Reasoning:
- The PRD treats the LLM as the final judge for understanding quality.
- Keeping all prompt logic on the backend protects the API key and prevents frontend duplication.

### 7. Build the thin frontend SPA
Create a simple React app with:
- login/signup screen
- concept entry form
- explanation form
- follow-up question forms
- final report view
- session history list

Reasoning:
- The frontend should stay dumb and focused on UX and API calls.
- It should not contain scoring logic or business rules beyond rendering state.

### 8. Add a minimal UX pass
Make the flow feel coherent and student-friendly:
- a single linear flow for the active session
- obvious progress between steps
- readable final report
- simple empty/loading/error states

Reasoning:
- The product is about clarity and feedback, so the interface should reinforce that.
- We can keep the design simple without making it feel unfinished.

### 9. Add local dev ergonomics
Provide environment docs and startup commands for:
- frontend dev server
- backend dev server
- required environment variables
- Supabase and NIM configuration

Reasoning:
- A project like this is only useful if it is easy to start and understand.
- Good docs will also make future iterations faster.

### 10. Verify the end-to-end flow
Smoke test the intended MVP behavior:
- authenticated user can create a session
- initial explanation is stored
- follow-up questions are generated
- answers are stored
- final evaluation is returned
- session history loads only the current user’s records

Reasoning:
- The PRD is flow-based, so we need one end-to-end sanity check more than isolated unit coverage.

## Suggested Build Order
1. Backend scaffold and settings
2. Auth verification
3. Database schema and RLS
4. Session and response endpoints
5. NIM integration
6. Frontend scaffold
7. Frontend flow wiring
8. Docs and smoke testing

## Out of Scope
- Leaderboards
- Sharing
- Gamification
- Admin panel
- Analytics dashboard
- RAG or vector databases
- Agent frameworks
- Collaborative features

## Definition of Done
- The app supports login/signup, concept submission, explanation, follow-up questions, final evaluation, and session history.
- The backend verifies Supabase JWTs on every protected request.
- The backend owns all writes and all LLM traffic.
- The database schema matches the PRD and enforces RLS.
- The frontend remains a thin SPA with no duplicated business logic.

## Progress Log

### 2026-06-20 - Initial scaffold started
- Added repo-level scaffolding for the MVP rather than waiting for a perfect first pass.
- Created the backend app structure with settings, JWT auth, a repository abstraction, session flow service, FastAPI routes, and a Supabase/Postgres schema file with RLS policies.
- Added a NIM client wrapper that uses the configured NVIDIA endpoint when available and falls back to deterministic local analysis so the app can still be exercised without secrets.
- Added the frontend Vite + React + TypeScript shell with Supabase auth hooks, API helpers, a linear session flow UI, session history, and a more intentional visual treatment.
- Added local development docs and environment examples for both apps.

### 2026-06-20 - Scaffold sanity pass
- Tightened the frontend session-switch behavior so explanation drafts and follow-up answers reset when the active session changes.
- Hid the follow-up form once a session reaches the complete state, which keeps the final report read-only after submission.
- Verified the Python backend sources with `python3 -m compileall backend/app` to catch syntax issues early.
