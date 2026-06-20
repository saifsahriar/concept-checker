from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.core.auth import AuthenticatedUser
from app.schemas.session import AnalysisOut, SessionDetailOut, SessionSummary
from app.services.nim import FinalEvaluation, InitialAnalysis, NimClient
from app.services.repository import Repository


class SessionService:
    def __init__(self, repository: Repository, nim_client: NimClient) -> None:
        self._repository = repository
        self._nim = nim_client

    @property
    def repository(self) -> Repository:
        return self._repository

    async def create_session(self, user: AuthenticatedUser, concept: str) -> dict[str, Any]:
        await self._repository.ensure_user(user.id, user.email)
        session = await self._repository.create_session(user.id, concept)
        return {
            "session_id": session["id"],
            "concept": session["concept"],
            "status": session["status"],
            "next_step": "initial_explanation",
        }

    async def record_initial_explanation(self, user: AuthenticatedUser, session_id: str, explanation: str) -> dict[str, Any]:
        session = await self._require_session(user.id, session_id)
        await self._repository.add_response(
            session_id=session_id,
            stage="initial",
            question="Explain this concept in your own words as if you were teaching a beginner.",
            answer=explanation,
        )
        initial_analysis = await self._nim.analyze_initial_explanation(session["concept"], explanation)
        await self._repository.add_response(
            session_id=session_id,
            stage="followup_1",
            question=initial_analysis.followup_questions[0],
            answer=None,
        )
        await self._repository.add_response(
            session_id=session_id,
            stage="followup_2",
            question=initial_analysis.followup_questions[1],
            answer=None,
        )
        await self._repository.update_session_summary(session_id, understanding_score=0, status="awaiting_followups")
        return {
            "knowledge_gap": initial_analysis.knowledge_gap,
            "strengths": initial_analysis.strengths,
            "weaknesses": initial_analysis.weaknesses,
            "followup_questions": initial_analysis.followup_questions,
        }

    async def record_followup_answers(self, user: AuthenticatedUser, session_id: str, answers: list[str]) -> dict[str, Any]:
        session = await self._require_session(user.id, session_id)
        responses = await self._repository.list_responses(session_id)
        initial_response = next((response for response in responses if response["stage"] == "initial"), None)
        followup_responses = [response for response in responses if response["stage"] in {"followup_1", "followup_2"}]
        if initial_response is None or len(followup_responses) < 2:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Initial explanation is required before follow-ups")

        for response, answer in zip(followup_responses, answers):
            await self._repository.update_response(session_id, response["stage"], answer)

        initial_analysis = await self._nim.analyze_initial_explanation(session["concept"], initial_response["answer"] or "")
        final_evaluation: FinalEvaluation = await self._nim.evaluate_final(
            session["concept"],
            initial_response["answer"] or "",
            [response["question"] for response in followup_responses],
            answers,
            initial_analysis.knowledge_gap,
        )
        analysis = await self._repository.store_analysis(
            session_id=session_id,
            knowledge_gap=final_evaluation.knowledge_gap,
            strengths=final_evaluation.strengths,
            weaknesses=final_evaluation.weaknesses,
            final_feedback=final_evaluation.final_feedback,
        )
        await self._repository.update_session_summary(session_id, final_evaluation.understanding_score, "complete")
        return {
            "session_id": session_id,
            "analysis": analysis,
            "understanding_score": final_evaluation.understanding_score,
            "status": "complete",
        }

    async def list_sessions(self, user: AuthenticatedUser) -> list[dict[str, Any]]:
        sessions = await self._repository.list_sessions(user.id)
        return [self._to_summary(session) for session in sessions]

    async def get_session_detail(self, user: AuthenticatedUser, session_id: str) -> dict[str, Any]:
        session = await self._require_session(user.id, session_id)
        responses = await self._repository.list_responses(session_id)
        analysis = await self._repository.get_analysis(session_id)
        return {
            "session": self._to_summary(session),
            "responses": responses,
            "analysis": analysis,
        }

    async def _require_session(self, user_id: str, session_id: str) -> dict[str, Any]:
        session = await self._repository.get_session(user_id, session_id)
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return session

    @staticmethod
    def _to_summary(session: dict[str, Any]) -> dict[str, Any]:
        return SessionSummary(
            id=session["id"],
            concept=session["concept"],
            understanding_score=session.get("understanding_score"),
            status=session["status"],
            created_at=session["created_at"],
        ).model_dump()
