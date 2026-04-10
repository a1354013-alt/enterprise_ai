from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from auth import extract_token_from_header, verify_token


logger = logging.getLogger("enterprise_ai")


async def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    token = extract_token_from_header(authorization)
    return verify_token(token)


async def get_current_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") != "admin":
        logger.warning("Admin access denied for user %s", current_user.get("sub"))
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required.",
        )
    return current_user
