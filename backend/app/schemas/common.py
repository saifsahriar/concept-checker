from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    ok: bool
    service: str


class DatabaseHealthResponse(BaseModel):
    ok: bool
    database: str


class ErrorResponse(BaseModel):
    detail: str


class UserOut(BaseModel):
    id: str
    email: str | None = None
    created_at: datetime | None = None
