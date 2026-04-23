"""네이버 쇼핑 검색 API 래퍼."""
from __future__ import annotations
import os
import re
import requests

ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"
_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    if not text:
        return ""
    return _TAG_RE.sub("", text).replace("&amp;", "&").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")


def search(keyword: str, limit: int = 10) -> list[dict]:
    cid = os.environ.get("NAVER_CLIENT_ID", "").strip()
    csecret = os.environ.get("NAVER_CLIENT_SECRET", "").strip()
    if not cid or not csecret:
        raise RuntimeError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET not configured")

    r = requests.get(
        ENDPOINT,
        params={
            "query": keyword,
            "display": max(1, min(limit, 100)),
            "sort": "sim",
        },
        headers={
            "X-Naver-Client-Id": cid,
            "X-Naver-Client-Secret": csecret,
        },
        timeout=8,
    )
    r.raise_for_status()
    data = r.json()

    items: list[dict] = []
    for i, it in enumerate(data.get("items", []) or []):
        items.append({
            "rank": i + 1,
            "title": _clean(str(it.get("title", "")))[:300],
            "price": str(it.get("lprice", "")),
            "currency": "원",
            "shop": str(it.get("mallName", ""))[:100],
            "url": str(it.get("link", "")),
            "image_url": str(it.get("image", "")),
            "source": "naver",
        })
    return items
