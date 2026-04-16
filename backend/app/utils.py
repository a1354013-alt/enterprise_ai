from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, status

from app.models import ROLE_VALUES


MAX_FILE_SIZE = 50 * 1024 * 1024
ALLOWED_FILE_EXTENSIONS = (".pdf", ".txt", ".md")
ALLOWED_ROLES = set(ROLE_VALUES)


def generate_safe_filename(original_filename: str) -> str:
    ext = Path(original_filename).suffix.lower()
    return f"{uuid.uuid4()}{ext}"


def validate_file_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_FILE_EXTENSIONS


def normalize_roles(roles: str | Iterable[str] | None, *, default: list[str] | None = None) -> list[str]:
    if default is None:
        default = ["user"]

    if roles is None:
        normalized = list(default)
    elif isinstance(roles, str):
        normalized = [part.strip() for part in roles.split(",") if part.strip()]
    else:
        normalized = [str(part).strip() for part in roles if str(part).strip()]

    if not normalized:
        normalized = list(default)

    invalid = [role for role in normalized if role not in ALLOWED_ROLES]
    if invalid:
        raise ValueError(f"Unsupported roles: {', '.join(invalid)}")

    deduplicated: list[str] = []
    for role in normalized:
        if role not in deduplicated:
            deduplicated.append(role)
    return deduplicated


async def stream_write_file(file, file_path: Path, max_size: int = MAX_FILE_SIZE, chunk_size: int = 8192) -> int:
    total_size = 0
    try:
        with open(file_path, 'wb') as output_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > max_size:
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the {max_size // (1024 * 1024)} MB limit.",
                    )
                output_file.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store uploaded file: {exc}",
        ) from exc

    return total_size


def get_env_list(key: str, default: list[str] | None = None) -> list[str]:
    if default is None:
        default = []
    value = os.getenv(key, '').strip()
    if not value:
        return list(default)
    return [item.strip() for item in value.split(',') if item.strip()]
