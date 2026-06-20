# PRD - Concept Checker

## Overview
Concept Checker is a simple web application that helps students determine whether they truly understand a concept or are only repeating definitions.

The application accepts a concept from the student, asks them to explain it in their own words, identifies gaps in understanding, asks targeted follow-up questions, and finally generates feedback.

The goal is not to test memorization. The goal is to verify conceptual understanding.

## Core Hypothesis
Many students can define a concept but cannot explain:

* Why it exists
* What problem it solves
* What happens without it

The application should identify those gaps.

## Tech Stack

**Frontend:**
* React + Vite + TypeScript
* Plain SPA, no SSR — the backend owns all business logic, so the frontend stays a thin client (forms + API calls)
* Hosted on Vercel

**Backend / API:**
* FastAPI (Python)
* Hosted on Render
* Verifies the Supabase JWT on every request (using Supabase's JWT secret) to identify the user — no separate auth system
* Owns all writes (sessions, responses, analysis) and all LLM calls

**Database:**
* Supabase (Postgres)
* Accessed from the backend only (via `supabase-py` or `asyncpg`), not from the frontend

**Authentication:**
* Supabase Auth
* Frontend handles login/signup directly with Supabase and gets a JWT
* Frontend sends that JWT to FastAPI on every request; FastAPI verifies it and extracts `user_id`
* Row Level Security stays on as a second line of defense in Postgres (see Security section below)

**LLM:**
* NVIDIA NIM
* Model: `nvidia/llama-3.3-nemotron-super-49b-v1`
* Base URL: `https://integrate.api.nvidia.com/v1`
* Called only from the FastAPI backend — API key never touches the frontend

**Why this split:** one backend (FastAPI) owns the database, the LLM key, and all logic. The frontend is dumb on purpose — it just renders steps and calls your API. Nothing duplicated, nothing to keep in sync, no Next.js/Python hybrid weirdness.

## User Workflow

**Step 1**
User signs in.

**Step 2**
User enters a concept.

Examples:
* API
* Database
* Photosynthesis
* Newton's Laws
* Supply and Demand

**Step 3**
System asks:
"Explain this concept in your own words as if you were teaching a beginner."
User submits explanation.

**Step 4**
LLM analyzes explanation and identifies the biggest knowledge gap.

Example:
Gap: User explained what a backend does but not why it is needed.

**Step 5**
LLM generates 2 follow-up questions targeting that specific gap.
User answers both questions.

**Step 6**
LLM evaluates:
* Initial explanation
* Follow-up answers

LLM determines:
* Understanding level
* Strengths
* Weaknesses
* Knowledge gap
* Whether the gap was closed

**Step 7**
Show final report.

Example:
Understanding Score: 72%

Strengths:
* Understands role of backend

Weaknesses:
* Does not fully understand security implications

Knowledge Gap:
* Why backend is necessary

Recommendation:
* Study authentication and secret management

## LLM Responsibilities (Probabilistic)
The LLM is responsible for:
* Understanding explanations
* Finding knowledge gaps
* Generating follow-up questions
* Evaluating answers
* Producing final feedback
* Producing final score

The LLM is also the final judge.

Accepted failure mode:
The LLM may occasionally overestimate understanding. This is acceptable for the MVP.

## Deterministic Components
The application handles:
* Authentication
* Session management
* Database operations
* Saving explanations
* Saving answers
* Saving analysis results
* Progress tracking
* Row Level Security

## Database Schema

**users**
`id` `email` `created_at`

**sessions**
`id` `user_id` `concept` `understanding_score` `created_at`
Relationship: Many sessions belong to one user.

**responses**
`id` `session_id` `stage` `question` `answer` `created_at`
`stage` values:
* initial
* followup_1
* followup_2

Relationship: Many responses belong to one session.

**analysis**
`id` `session_id` `knowledge_gap` `strengths` `weaknesses` `final_feedback` `created_at`
Relationship: One analysis belongs to one session.

## Relationships
User → many Sessions
Session → many Responses
Session → one Analysis

## Security
Enable RLS on:
* sessions
* responses
* analysis

Policy:
Users can only access rows where:
`user_id = auth.uid()`

## MVP Scope

**Must Have:**
* Login
* Concept input
* Initial explanation
* LLM gap analysis
* Two follow-up questions
* Final evaluation report
* Session history

**Do Not Build:**
* Leaderboards
* Gamification
* Sharing
* Multi-user collaboration
* Admin panel
* Analytics dashboard
* Complex scoring systems
* Vector databases
* RAG
* Agent frameworks

Keep everything simple and functional.