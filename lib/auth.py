"""공유 토큰 기반 인증. 상수시간 비교로 타이밍 공격 방어."""
from __future__ import annotations
import hmac
import os


def verify_token(provided: str | None) -> bool:
    expected = os.environ.get("SADO_PROXY_TOKEN", "")
    if not expected or len(expected) < 16:
        return False
    if not provided:
        return False
    return hmac.compare_digest(expected, provided)
