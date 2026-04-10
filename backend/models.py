from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


ROLE_VALUES = ("employee", "manager", "hr", "admin")


class MessageResponse(BaseModel):
    message: str


class LoginRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    user_id: str
    role: str
    display_name: str


class Source(BaseModel):
    doc_name: str
    chunk_text: str
    page_or_section: str


class QARequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class QAResponse(BaseModel):
    answer: str
    sources: list[Source] = Field(default_factory=list)


class GenerateRequest(BaseModel):
    template_type: str = Field(min_length=1, max_length=100)
    inputs: dict[str, Any] = Field(default_factory=dict)


class GenerateResponse(BaseModel):
    content: str


class DocumentResponse(BaseModel):
    id: str
    filename: str
    allowed_roles: list[str]
    uploaded_at: datetime | str
    file_size: int
    uploaded_by: str | None = None
    approved: int
    is_active: int


class UploadDocumentResponse(DocumentResponse):
    message: str


class AdminUserResponse(BaseModel):
    user_id: str
    display_name: str
    role: str
    is_active: int
    created_at: datetime | str
    updated_at: datetime | str


class AdminUserCreateRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=255)
    display_name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="employee")
    is_active: int = Field(default=1)


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=255)
    role: str | None = None
    is_active: int | None = None


class AdminDocumentUpdateRequest(BaseModel):
    allowed_roles: list[str] | None = None
    approved: int | None = None
    is_active: int | None = None


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    version: str
