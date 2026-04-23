"""
eBay Browse API 래퍼 — 스켈레톤.
다음 주 연동 예정. OAuth 2.0 client_credentials 플로우 필요.

흐름:
  1) POST https://api.ebay.com/identity/v1/oauth2/token
     (basic auth: client_id:client_secret, scope=https://api.ebay.com/oauth/api_scope)
     → access_token (약 2시간 유효, 메모리 캐시)
  2) GET https://api.ebay.com/buy/browse/v1/item_summary/search?q=<kw>&limit=<n>
     Authorization: Bearer <access_token>
"""
from __future__ import annotations
import os


def search(keyword: str, limit: int = 10) -> list[dict]:
    cid = os.environ.get("EBAY_CLIENT_ID", "").strip()
    csecret = os.environ.get("EBAY_CLIENT_SECRET", "").strip()
    if not cid or not csecret:
        raise NotImplementedError("eBay source는 다음 주 추가 예정 (EBAY_CLIENT_ID/SECRET 미설정)")

    # TODO(next-week): OAuth token 발급 + Browse API 호출 + 응답 정규화
    raise NotImplementedError("eBay 연동은 다음 주 작업")
