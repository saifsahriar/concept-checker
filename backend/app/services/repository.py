from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import UUID, uuid4

import asyncpg


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Repository(Protocol):
    async def ensure_user(self, user_id: str, email: str | None) -> dict[str, Any]: ...
    async def create_session(self, user_id: str, concept: str) -> dict[str, Any]: ...
    async def list_sessions(self, user_id: str) -> list[dict[str, Any]]: ...
    async def get_session(self, user_id: str, session_id: str) -> dict[str, Any] | None: ...
    async def add_response(self, session_id: str, stage: str, question: str, answer: str | None) -> dict[str, Any]: ...
    async def update_response(self, session_id: str, stage: str, answer: str) -> dict[str, Any] | None: ...
    async def list_responses(self, session_id: str) -> list[dict[str, Any]]: ...
    async def store_analysis(
        self,
        session_id: str,
        knowledge_gap: str,
        strengths: str,
        weaknesses: str,
        final_feedback: str,
    ) -> dict[str, Any]: ...
    async def update_session_summary(self, session_id: str, understanding_score: int, status: str) -> dict[str, Any] | None: ...
    async def get_analysis(self, session_id: str) -> dict[str, Any] | None: ...
    async def health_check(self) -> bool: ...


@dataclass(slots=True)
class MemoryRepository:
    users: dict[str, dict[str, Any]]
    sessions: dict[str, dict[str, Any]]
    responses: dict[str, dict[str, Any]]
    analysis: dict[str, dict[str, Any]]

    def __init__(self) -> None:
        self.users = {}
        self.sessions = {}
        self.responses = {}
        self.analysis = {}

    async def ensure_user(self, user_id: str, email: str | None) -> dict[str, Any]:
        record = self.users.get(user_id)
        if record is None:
            record = {"id": user_id, "email": email, "created_at": _now()}
            self.users[user_id] = record
        elif email and record.get("email") != email:
            record["email"] = email
        return record

    async def create_session(self, user_id: str, concept: str) -> dict[str, Any]:
        session_id = str(uuid4())
        record = {
            "id": session_id,
            "user_id": user_id,
            "concept": concept,
            "understanding_score": None,
            "status": "awaiting_initial_explanation",
            "created_at": _now(),
        }
        self.sessions[session_id] = record
        return record

    async def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        return sorted(
            [session for session in self.sessions.values() if session["user_id"] == user_id],
            key=lambda item: item["created_at"],
            reverse=True,
        )

    async def get_session(self, user_id: str, session_id: str) -> dict[str, Any] | None:
        session = self.sessions.get(session_id)
        if session and session["user_id"] == user_id:
            return session
        return None

    async def add_response(self, session_id: str, stage: str, question: str, answer: str | None) -> dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "session_id": session_id,
            "stage": stage,
            "question": question,
            "answer": answer,
            "created_at": _now(),
        }
        self.responses[record["id"]] = record
        return record

    async def update_response(self, session_id: str, stage: str, answer: str) -> dict[str, Any] | None:
        for record in self.responses.values():
            if record["session_id"] == session_id and record["stage"] == stage:
                record["answer"] = answer
                return record
        return None

    async def list_responses(self, session_id: str) -> list[dict[str, Any]]:
        return sorted(
            [response for response in self.responses.values() if response["session_id"] == session_id],
            key=lambda item: item["created_at"],
        )

    async def store_analysis(
        self,
        session_id: str,
        knowledge_gap: str,
        strengths: str,
        weaknesses: str,
        final_feedback: str,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid4()),
            "session_id": session_id,
            "knowledge_gap": knowledge_gap,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "final_feedback": final_feedback,
            "created_at": _now(),
        }
        self.analysis[session_id] = record
        return record

    async def update_session_summary(self, session_id: str, understanding_score: int, status: str) -> dict[str, Any] | None:
        session = self.sessions.get(session_id)
        if not session:
            return None
        session["understanding_score"] = understanding_score
        session["status"] = status
        return session

    async def get_analysis(self, session_id: str) -> dict[str, Any] | None:
        return self.analysis.get(session_id)

    async def health_check(self) -> bool:
        return True


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self._database_url)

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def ensure_user(self, user_id: str, email: str | None) -> dict[str, Any]:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            insert into public.users (id, email)
            values ($1::uuid, $2)
            on conflict (id) do update set email = excluded.email
            returning id::text as id, email, created_at
            """,
            user_id,
            email,
        )
        return dict(row)

    async def create_session(self, user_id: str, concept: str) -> dict[str, Any]:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            insert into public.sessions (user_id, concept)
            values ($1::uuid, $2)
            returning id::text as id, user_id::text as user_id, concept, understanding_score, status, created_at
            """,
            user_id,
            concept,
        )
        return dict(row)

    async def list_sessions(self, user_id: str) -> list[dict[str, Any]]:
        await self.connect()
        assert self._pool is not None
        rows = await self._pool.fetch(
            """
            select id::text as id, user_id::text as user_id, concept, understanding_score, status, created_at
            from public.sessions
            where user_id = $1::uuid
            order by created_at desc
            """,
            user_id,
        )
        return [dict(row) for row in rows]

    async def get_session(self, user_id: str, session_id: str) -> dict[str, Any] | None:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            select id::text as id, user_id::text as user_id, concept, understanding_score, status, created_at
            from public.sessions
            where id = $1::uuid and user_id = $2::uuid
            """,
            session_id,
            user_id,
        )
        return dict(row) if row else None

    async def add_response(self, session_id: str, stage: str, question: str, answer: str | None) -> dict[str, Any]:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            insert into public.responses (session_id, stage, question, answer)
            values ($1::uuid, $2, $3, $4)
            returning id::text as id, session_id::text as session_id, stage, question, answer, created_at
            """,
            session_id,
            stage,
            question,
            answer,
        )
        return dict(row)

    async def update_response(self, session_id: str, stage: str, answer: str) -> dict[str, Any] | None:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            update public.responses
            set answer = $3
            where session_id = $1::uuid and stage = $2
            returning id::text as id, session_id::text as session_id, stage, question, answer, created_at
            """,
            session_id,
            stage,
            answer,
        )
        return dict(row) if row else None

    async def list_responses(self, session_id: str) -> list[dict[str, Any]]:
        await self.connect()
        assert self._pool is not None
        rows = await self._pool.fetch(
            """
            select id::text as id, session_id::text as session_id, stage, question, answer, created_at
            from public.responses
            where session_id = $1::uuid
            order by created_at asc
            """,
            session_id,
        )
        return [dict(row) for row in rows]

    async def store_analysis(
        self,
        session_id: str,
        knowledge_gap: str,
        strengths: str,
        weaknesses: str,
        final_feedback: str,
    ) -> dict[str, Any]:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            insert into public.analysis (session_id, knowledge_gap, strengths, weaknesses, final_feedback)
            values ($1::uuid, $2, $3, $4, $5)
            returning id::text as id, session_id::text as session_id, knowledge_gap, strengths, weaknesses, final_feedback, created_at
            """,
            session_id,
            knowledge_gap,
            strengths,
            weaknesses,
            final_feedback,
        )
        return dict(row)

    async def update_session_summary(self, session_id: str, understanding_score: int, status: str) -> dict[str, Any] | None:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            update public.sessions
            set understanding_score = $2, status = $3
            where id = $1::uuid
            returning id::text as id, user_id::text as user_id, concept, understanding_score, status, created_at
            """,
            session_id,
            understanding_score,
            status,
        )
        return dict(row) if row else None

    async def get_analysis(self, session_id: str) -> dict[str, Any] | None:
        await self.connect()
        assert self._pool is not None
        row = await self._pool.fetchrow(
            """
            select id::text as id, session_id::text as session_id, knowledge_gap, strengths, weaknesses, final_feedback, created_at
            from public.analysis
            where session_id = $1::uuid
            order by created_at desc
            limit 1
            """,
            session_id,
        )
        return dict(row) if row else None

    async def health_check(self) -> bool:
        await self.connect()
        assert self._pool is not None
        await self._pool.execute("select 1")
        return True


def build_repository(database_url: str | None) -> Repository:
    if database_url:
        return PostgresRepository(database_url)
    return MemoryRepository()
