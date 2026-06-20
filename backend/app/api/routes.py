from fastapi import APIRouter, Depends

from app.core.auth import AuthenticatedUser, get_current_user
from app.schemas.common import DatabaseHealthResponse, HealthResponse, UserOut
from app.schemas.session import (
    CreateSessionRequest,
    FollowupAnswersRequest,
    FollowupResponseOut,
    InitialAnalysisOut,
    InitialExplanationRequest,
    SessionCreateResponse,
    SessionDetailOut,
    SessionSummary,
)
from app.services.session_service import SessionService


def build_router(session_service: SessionService) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(ok=True, service="concept-checker-api")

    @router.get("/db-health", response_model=DatabaseHealthResponse)
    async def db_health() -> DatabaseHealthResponse:
        ok = await session_service.repository.health_check()
        return DatabaseHealthResponse(ok=ok, database="reachable")

    @router.get("/me", response_model=UserOut)
    async def me(current_user: AuthenticatedUser = Depends(get_current_user)) -> UserOut:
        return UserOut(id=current_user.id, email=current_user.email)

    @router.post("/sessions", response_model=SessionCreateResponse)
    async def create_session(
        payload: CreateSessionRequest,
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> SessionCreateResponse:
        data = await session_service.create_session(current_user, payload.concept)
        return SessionCreateResponse(**data)

    @router.post("/sessions/{session_id}/initial-explanation", response_model=InitialAnalysisOut)
    async def initial_explanation(
        session_id: str,
        payload: InitialExplanationRequest,
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> InitialAnalysisOut:
        data = await session_service.record_initial_explanation(current_user, session_id, payload.explanation)
        return InitialAnalysisOut(**data)

    @router.post("/sessions/{session_id}/followups", response_model=FollowupResponseOut)
    async def followups(
        session_id: str,
        payload: FollowupAnswersRequest,
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> FollowupResponseOut:
        data = await session_service.record_followup_answers(current_user, session_id, payload.answers)
        return FollowupResponseOut(**data)

    @router.get("/sessions", response_model=list[SessionSummary])
    async def list_sessions(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> list[SessionSummary]:
        return [SessionSummary(**item) for item in await session_service.list_sessions(current_user)]

    @router.get("/sessions/{session_id}", response_model=SessionDetailOut)
    async def session_detail(
        session_id: str,
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> SessionDetailOut:
        data = await session_service.get_session_detail(current_user, session_id)
        return SessionDetailOut(**data)

    return router
