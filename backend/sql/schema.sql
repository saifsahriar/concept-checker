create extension if not exists pgcrypto;

create table if not exists public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null,
  created_at timestamptz not null default now()
);

create table if not exists public.sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  concept text not null,
  understanding_score integer,
  status text not null default 'awaiting_initial_explanation',
  created_at timestamptz not null default now()
);

create table if not exists public.responses (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions (id) on delete cascade,
  stage text not null,
  question text not null,
  answer text,
  created_at timestamptz not null default now()
);

create table if not exists public.analysis (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.sessions (id) on delete cascade,
  knowledge_gap text not null,
  strengths text not null,
  weaknesses text not null,
  final_feedback text not null,
  created_at timestamptz not null default now()
);

alter table public.users enable row level security;
alter table public.sessions enable row level security;
alter table public.responses enable row level security;
alter table public.analysis enable row level security;

drop policy if exists "Users can read their profile" on public.users;
create policy "Users can read their profile"
  on public.users
  for select
  using (id = auth.uid());

drop policy if exists "Users can insert their profile" on public.users;
create policy "Users can insert their profile"
  on public.users
  for insert
  with check (id = auth.uid());

drop policy if exists "Users can read their sessions" on public.sessions;
create policy "Users can read their sessions"
  on public.sessions
  for select
  using (user_id = auth.uid());

drop policy if exists "Users can insert their sessions" on public.sessions;
create policy "Users can insert their sessions"
  on public.sessions
  for insert
  with check (user_id = auth.uid());

drop policy if exists "Users can update their sessions" on public.sessions;
create policy "Users can update their sessions"
  on public.sessions
  for update
  using (user_id = auth.uid());

drop policy if exists "Users can read their responses" on public.responses;
create policy "Users can read their responses"
  on public.responses
  for select
  using (
    session_id in (select id from public.sessions where user_id = auth.uid())
  );

drop policy if exists "Users can insert their responses" on public.responses;
create policy "Users can insert their responses"
  on public.responses
  for insert
  with check (
    session_id in (select id from public.sessions where user_id = auth.uid())
  );

drop policy if exists "Users can update their responses" on public.responses;
create policy "Users can update their responses"
  on public.responses
  for update
  using (
    session_id in (select id from public.sessions where user_id = auth.uid())
  );

drop policy if exists "Users can read their analysis" on public.analysis;
create policy "Users can read their analysis"
  on public.analysis
  for select
  using (
    session_id in (select id from public.sessions where user_id = auth.uid())
  );

drop policy if exists "Users can insert their analysis" on public.analysis;
create policy "Users can insert their analysis"
  on public.analysis
  for insert
  with check (
    session_id in (select id from public.sessions where user_id = auth.uid())
  );
