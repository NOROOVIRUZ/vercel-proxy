"""
매우 간단한 슬라이딩-윈도우 레이트리밋.
Vercel Serverless는 인스턴스가 여러 개라 per-instance 기준으로만 동작한다.
엄격한 글로벌 제한이 필요하면 추후 Upstash Redis 로 교체할 것.
"""
from __future__ import annotations
import os
import time
from collections import deque
from threading import Lock

_buckets: dict[str, deque] = {}
_lock = Lock()


def _limit_per_min() -> int:
    try:
        return max(1, int(os.environ.get("SADO_RATE_LIMIT_PER_MIN", "30")))
    except ValueError:
        return 30


def check(key: str) -> bool:
    now = time.time()
    cutoff = now - 60.0
    cap = _limit_per_min()
    with _lock:
        bucket = _buckets.setdefault(key, deque())
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= cap:
            return False
        bucket.append(now)
    return True
