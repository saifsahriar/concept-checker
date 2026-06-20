from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import build_router
from app.core.config import get_settings
from app.services.nim import NimClient
from app.services.repository import MemoryRepository, PostgresRepository, build_repository
from app.services.session_service import SessionService


def create_app() -> FastAPI:
    settings = get_settings()
    repository = build_repository(settings.database_url)
    nim_client = NimClient(settings)
    session_service = SessionService(repository, nim_client)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if isinstance(repository, PostgresRepository):
            await repository.close()
        await nim_client.close()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(build_router(session_service))
    return app


app = create_app()
