"""CORS 허용 Origin 판정. 환경변수의 콤마 구분 리스트와 정확 일치한 경우만 허용."""
from __future__ import annotations
import os


def allowed_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    raw = os.environ.get("SADO_ALLOWED_ORIGIN", "http://127.0.0.1:5000")
    allowed = {o.strip() for o in raw.split(",") if o.strip()}
    return origin if origin in allowed else None
