"""
Vercel Serverless Function — 소싱 검색 프록시.

GET /api/search?source=<rakuten|naver|ebay>&q=<keyword>&limit=<n>

Headers:
  X-Sado-Token: <공유 토큰>   (필수)

응답:
  200 {"source": "...", "keyword": "...", "items": [...]}
  400 invalid_source / invalid_keyword
  401 unauthorized
  429 rate_limited
  501 not_implemented (아직 연동 안 된 소스)
  502 upstream_error (외부 API 장애)
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import sys
from pathlib import Path

# Vercel Python runtime은 repo 루트를 sys.path 에 포함시키지 않으므로
# api/ 기준 상대로 lib/ 를 import 할 수 있게 한 줄 추가한다.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.auth import verify_token  # noqa: E402
from lib.cors import allowed_origin  # noqa: E402
from lib.ratelimit import check as ratelimit_check  # noqa: E402
from lib import sources  # noqa: E402

MAX_KEYWORD = 100
MAX_LIMIT = 30


class handler(BaseHTTPRequestHandler):
    # ─── 공통 응답 유틸 ───
    def _send(self, status: int, body: dict, origin: str | None = None) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(raw)

    # CORS preflight
    def do_OPTIONS(self) -> None:
        origin = allowed_origin(self.headers.get("Origin"))
        self.send_response(204)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Headers", "X-Sado-Token, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Max-Age", "86400")
            self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:
        origin = allowed_origin(self.headers.get("Origin"))
        token = self.headers.get("X-Sado-Token")

        # 1) 인증
        if not verify_token(token):
            return self._send(401, {"error": "unauthorized"}, origin)

        # 2) Rate limit (토큰이 통과한 경우만 — 익명 스캔에 버킷이 안 쌓이도록)
        #    key 는 토큰의 prefix 사용 (동일 토큰 = 동일 버킷)
        rl_key = (token or "")[:16]
        if not ratelimit_check(rl_key):
            return self._send(429, {"error": "rate_limited"}, origin)

        # 3) 파라미터
        qs = parse_qs(urlparse(self.path).query)
        source = (qs.get("source", [""])[0] or "").strip().lower()
        keyword = (qs.get("q", [""])[0] or "").strip()
        try:
            limit = int(qs.get("limit", ["10"])[0])
        except ValueError:
            limit = 10
        limit = max(1, min(limit, MAX_LIMIT))

        if not keyword or len(keyword) > MAX_KEYWORD:
            return self._send(400, {"error": "invalid_keyword"}, origin)

        fn = sources.get(source)
        if fn is None:
            return self._send(
                400,
                {"error": "invalid_source", "allowed": sources.available()},
                origin,
            )

        # 4) 호출
        try:
            items = fn(keyword, limit)
        except NotImplementedError as e:
            return self._send(501, {"error": "not_implemented", "message": str(e)}, origin)
        except Exception as e:
            # 응답 바디는 로그에 안 남김. 최소 진단 정보만.
            print(
                f"[search] upstream_error source={source} kw_len={len(keyword)} err={type(e).__name__}: {e}",
                file=sys.stderr,
            )
            return self._send(502, {"error": "upstream_error", "debug_type": type(e).__name__, "debug_msg": str(e)[:300]}, origin)

        return self._send(
            200,
            {"source": source, "keyword": keyword, "items": items},
            origin,
        )
