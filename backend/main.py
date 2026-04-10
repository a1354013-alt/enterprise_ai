from __future__ import annotations

import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from auth import create_token
from database import DocumentDatabase, delete_from_vector_db
from dependencies import get_current_admin, get_current_user
from models import (
    AdminDocumentUpdateRequest,
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserUpdateRequest,
    DocumentResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    LoginRequest,
    LoginResponse,
    MeResponse,
    MessageResponse,
    QARequest,
    QAResponse,
    UploadDocumentResponse,
)
from services import FORM_TEMPLATES, generate_form, perform_qa, process_file
from utils import generate_safe_filename, get_env_list, normalize_roles, stream_write_file, validate_file_extension


load_dotenv()

APP_VERSION = "4.2.0"
logger = logging.getLogger("enterprise_ai")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

db = DocumentDatabase(os.getenv("DATABASE_PATH", "documents.db"))

allowed_origins = get_env_list("ALLOWED_ORIGINS", ["http://localhost:5173"])
allow_credentials = "*" not in allowed_origins


def serialize_me(current_user: dict) -> MeResponse:
    return MeResponse(
        user_id=current_user["sub"],
        role=current_user["role"],
        display_name=current_user.get("display_name", ""),
    )


def serialize_document(document: dict) -> DocumentResponse:
    return DocumentResponse(
        id=document["doc_id"],
        filename=document["filename"],
        allowed_roles=document["allowed_roles"],
        uploaded_at=document["uploaded_at"],
        file_size=int(document.get("file_size", 0)),
        uploaded_by=document.get("uploaded_by"),
        approved=int(document.get("approved", 0)),
        is_active=int(document.get("is_active", 1)),
    )


def safe_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except PermissionError:
        logger.warning("Could not delete file %s because it is locked by the OS.", path)


async def sync_document_index(document: dict) -> None:
    delete_from_vector_db(document["doc_id"])
    if int(document["approved"]) != 1 or int(document["is_active"]) != 1:
        return

    file_path = UPLOAD_DIR / document["saved_filename"]
    if not file_path.exists():
        raise FileNotFoundError(f"Document file is missing: {file_path}")

    await asyncio.to_thread(
        process_file,
        document["doc_id"],
        str(file_path),
        document["filename"],
        document["allowed_roles"],
        int(document["approved"]),
        int(document["is_active"]),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Enterprise AI Assistant API starting.")
    logger.info("CORS origins: %s", allowed_origins)
    yield
    logger.info("Enterprise AI Assistant API stopped.")


app = FastAPI(
    title="Enterprise AI Assistant API",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in allowed_origins else allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", version=APP_VERSION)


@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    if not db.verify_password(request.user_id, request.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    user = db.get_user(request.user_id)
    if not user or int(user["is_active"]) != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive.")

    return LoginResponse(
        access_token=create_token(
            user_id=request.user_id,
            role=user["role"],
            display_name=user["display_name"],
        )
    )


@app.get("/api/me", response_model=MeResponse)
async def me(current_user: dict = Depends(get_current_user)) -> MeResponse:
    return serialize_me(current_user)


@app.post("/api/docs/upload", response_model=UploadDocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    allowed_roles: str = Form("employee"),
    current_user: dict = Depends(get_current_user),
) -> UploadDocumentResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename.")
    if not validate_file_extension(file.filename):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type.")

    roles = normalize_roles(allowed_roles)
    safe_filename = generate_safe_filename(file.filename)
    file_path = UPLOAD_DIR / safe_filename
    file_size = await stream_write_file(file, file_path)

    doc_id = str(uuid.uuid4())
    if not db.add_document(
        doc_id=doc_id,
        filename=file.filename,
        saved_filename=safe_filename,
        allowed_roles=roles,
        file_size=file_size,
        uploaded_by=current_user["sub"],
    ):
        safe_unlink(file_path)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to persist document.")

    document = db.get_document(doc_id)
    logger.info("Uploaded document %s by %s", doc_id, current_user["sub"])
    return UploadDocumentResponse(
        **serialize_document(document).model_dump(),
        message="Document uploaded and waiting for admin approval.",
    )


@app.get("/api/docs", response_model=list[DocumentResponse])
async def list_documents(current_user: dict = Depends(get_current_user)) -> list[DocumentResponse]:
    user_id = current_user["sub"]
    user_role = current_user["role"]
    visible: list[DocumentResponse] = []
    for document in db.list_documents():
        is_owner = document.get("uploaded_by") == user_id
        is_admin = user_role == "admin"
        is_visible = (
            int(document.get("approved", 0)) == 1
            and int(document.get("is_active", 1)) == 1
            and user_role in document["allowed_roles"]
        )
        if is_owner or is_admin or is_visible:
            visible.append(serialize_document(document))
    return visible


@app.delete("/api/docs/{doc_id}", response_model=MessageResponse)
async def delete_own_document(doc_id: str, current_user: dict = Depends(get_current_user)) -> MessageResponse:
    document = db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if current_user["role"] != "admin" and document.get("uploaded_by") != current_user["sub"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete this document.")

    delete_from_vector_db(doc_id)
    safe_unlink(UPLOAD_DIR / document["saved_filename"])
    db.delete_document(doc_id)
    return MessageResponse(message="Document deleted.")


@app.post("/api/qa", response_model=QAResponse)
async def qa(request: QARequest, current_user: dict = Depends(get_current_user)) -> QAResponse:
    answer, sources = await perform_qa(request.question, current_user["role"])
    logger.info("QA request by %s returned %s sources", current_user["sub"], len(sources))
    return QAResponse(answer=answer, sources=sources)


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, current_user: dict = Depends(get_current_user)) -> GenerateResponse:
    content = await generate_form(request.template_type, request.inputs, current_user["role"])
    return GenerateResponse(content=content)


@app.get("/api/admin/users", response_model=list[AdminUserResponse])
async def admin_list_users(current_admin: dict = Depends(get_current_admin)) -> list[AdminUserResponse]:
    _ = current_admin
    return [AdminUserResponse(**user) for user in db.list_users()]


@app.post("/api/admin/users", response_model=MessageResponse)
async def admin_create_user(
    request: AdminUserCreateRequest,
    current_admin: dict = Depends(get_current_admin),
) -> MessageResponse:
    _ = current_admin
    role = normalize_roles([request.role], default=["employee"])[0]
    if request.is_active not in (0, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="is_active must be 0 or 1.")

    created = db.add_user(
        user_id=request.user_id,
        password=request.password,
        display_name=request.display_name,
        role=role,
        is_active=request.is_active,
    )
    if not created:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists.")
    return MessageResponse(message="User created.")


@app.patch("/api/admin/users/{user_id}", response_model=MessageResponse)
async def admin_update_user(
    user_id: str,
    request: AdminUserUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
) -> MessageResponse:
    _ = current_admin
    updates = request.model_dump(exclude_none=True)
    if "role" in updates:
        updates["role"] = normalize_roles([updates["role"]], default=["employee"])[0]
    if "is_active" in updates and updates["is_active"] not in (0, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="is_active must be 0 or 1.")
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No user fields provided.")
    if not db.update_user(user_id, **updates):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return MessageResponse(message="User updated.")


@app.get("/api/admin/docs", response_model=list[DocumentResponse])
async def admin_list_documents(current_admin: dict = Depends(get_current_admin)) -> list[DocumentResponse]:
    _ = current_admin
    return [serialize_document(document) for document in db.list_documents()]


@app.patch("/api/admin/docs/{doc_id}", response_model=MessageResponse)
async def admin_update_document(
    doc_id: str,
    request: AdminDocumentUpdateRequest,
    current_admin: dict = Depends(get_current_admin),
) -> MessageResponse:
    _ = current_admin
    original = db.get_document(doc_id)
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    updates = request.model_dump(exclude_none=True)
    if "allowed_roles" in updates:
        updates["allowed_roles"] = normalize_roles(updates["allowed_roles"])
    if "approved" in updates and updates["approved"] not in (0, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="approved must be 0 or 1.")
    if "is_active" in updates and updates["is_active"] not in (0, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="is_active must be 0 or 1.")
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No document fields provided.")

    if not db.update_document(doc_id, **updates):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update document.")

    updated = db.get_document(doc_id)
    try:
        await sync_document_index(updated)
    except Exception as exc:
        db.update_document(
            doc_id,
            allowed_roles=original["allowed_roles"],
            approved=original["approved"],
            is_active=original["is_active"],
        )
        await sync_document_index(original)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to synchronize document index: {exc}",
        ) from exc

    return MessageResponse(message="Document updated.")


@app.delete("/api/admin/docs/{doc_id}", response_model=MessageResponse)
async def admin_delete_document(doc_id: str, current_admin: dict = Depends(get_current_admin)) -> MessageResponse:
    _ = current_admin
    document = db.get_document(doc_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    delete_from_vector_db(doc_id)
    safe_unlink(UPLOAD_DIR / document["saved_filename"])
    db.delete_document(doc_id)
    return MessageResponse(message="Document deleted.")


@app.get("/api/meta/templates")
async def list_templates(current_user: dict = Depends(get_current_user)) -> dict[str, list[dict[str, object]]]:
    _ = current_user
    return {
        "templates": [
            {"value": key, "label": key.replace("_", " ").title(), "fields": value["fields"]}
            for key, value in FORM_TEMPLATES.items()
        ]
    }
