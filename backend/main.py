from __future__ import annotations

"""Compatibility entrypoint for running the API with uvicorn.

Prefer: `python -m uvicorn app.main:app ...`
"""

from app.main import app  # noqa: F401

